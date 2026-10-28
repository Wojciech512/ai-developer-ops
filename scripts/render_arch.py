#!/usr/bin/env python3
"""Render docs/architecture.{puml,md} from docs/architecture.model.json.

The renderer is a pure function of the model: it validates and formats, it
never analyses project code. See openspec/changes/ops-discover/design.md
for the frozen schema and the ordering, aggregation and preservation rules.
"""
import argparse
import json
import re
import sys

# Fixed order. Participant order and box order both derive from this, so the
# layout cannot depend on the order entries happen to appear in the model.
LAYERS = (
    "actor",
    "ui",
    "api",
    "service",
    "repository",
    "data",
    "integration",
)
FLOW_KINDS = ("main", "independent")

TOP_FIELDS = {"title", "components", "flows", "interactions"}
COMPONENT_FIELDS = {"id", "label", "layer", "path"}
FLOW_FIELDS = {"id", "label", "kind"}
INTERACTION_FIELDS = {"flow", "from", "to", "verb", "op", "seq"}

COMPONENT_ID_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
FLOW_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")

# Reserved for generated aggregates so a model id can never collide with one.
AGGREGATE_SUFFIX = "Group"


class ModelError(Exception):
    """Raised when the model cannot be read at all."""


def load_model(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise ModelError(f"model not found: {path}")
    except json.JSONDecodeError as exc:
        raise ModelError(f"invalid JSON in {path}: {exc}")


def _check_fields(entry, allowed, where, errors):
    unknown = sorted(set(entry) - allowed)
    for field in unknown:
        errors.append(f"{where}: unknown field {field!r}")
    missing = sorted(allowed - set(entry))
    for field in missing:
        errors.append(f"{where}: missing field {field!r}")
    return not unknown and not missing


def _validate_components(model, errors):
    components = model.get("components")
    if not isinstance(components, list) or not components:
        errors.append("components: must be a non-empty list")
        return []
    seen = set()
    for index, component in enumerate(components):
        where = f"components[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{where}: must be an object")
            continue
        if not _check_fields(component, COMPONENT_FIELDS, where, errors):
            continue
        cid = component["id"]
        if not isinstance(cid, str) or not COMPONENT_ID_RE.match(cid):
            errors.append(
                f"{where}: id {cid!r} must match {COMPONENT_ID_RE.pattern}"
            )
        elif cid.endswith(AGGREGATE_SUFFIX):
            errors.append(
                f"{where}: id {cid!r} must not end with "
                f"{AGGREGATE_SUFFIX!r} (reserved for aggregates)"
            )
        elif cid in seen:
            errors.append(f"{where}: duplicate id {cid!r}")
        else:
            seen.add(cid)
        if component["layer"] not in LAYERS:
            errors.append(
                f"{where}: layer {component['layer']!r} is not one of "
                f"{', '.join(LAYERS)}"
            )
    return components


def _validate_flows(model, errors):
    flows = model.get("flows")
    if not isinstance(flows, list) or not flows:
        errors.append("flows: must be a non-empty list")
        return []
    seen = set()
    mains = []
    for index, flow in enumerate(flows):
        where = f"flows[{index}]"
        if not isinstance(flow, dict):
            errors.append(f"{where}: must be an object")
            continue
        if not _check_fields(flow, FLOW_FIELDS, where, errors):
            continue
        fid = flow["id"]
        if not isinstance(fid, str) or not FLOW_ID_RE.match(fid):
            errors.append(
                f"{where}: id {fid!r} must match {FLOW_ID_RE.pattern}"
            )
        elif fid in seen:
            errors.append(f"{where}: duplicate id {fid!r}")
        else:
            seen.add(fid)
        if flow["kind"] not in FLOW_KINDS:
            errors.append(
                f"{where}: kind {flow['kind']!r} is not one of "
                f"{', '.join(FLOW_KINDS)}"
            )
        if flow.get("kind") == "main":
            mains.append(fid)
    if len(mains) != 1:
        errors.append(
            f"flows: exactly one flow must have kind 'main', found "
            f"{len(mains)} ({', '.join(mains) or 'none'})"
        )
    return flows


def _validate_interactions(model, errors, component_ids, flow_ids):
    interactions = model.get("interactions")
    if not isinstance(interactions, list) or not interactions:
        errors.append("interactions: must be a non-empty list")
        return []
    for index, interaction in enumerate(interactions):
        where = f"interactions[{index}]"
        if not isinstance(interaction, dict):
            errors.append(f"{where}: must be an object")
            continue
        if not _check_fields(interaction, INTERACTION_FIELDS, where, errors):
            continue
        if interaction["flow"] not in flow_ids:
            errors.append(
                f"{where}: flow {interaction['flow']!r} has no matching flow"
            )
        for end in ("from", "to"):
            if interaction[end] not in component_ids:
                errors.append(
                    f"{where}: {end} {interaction[end]!r} has no "
                    f"matching component"
                )
        seq = interaction["seq"]
        # bool is a subclass of int; a true/false seq is a typo, not an order.
        if type(seq) is not int:
            errors.append(f"{where}: seq {seq!r} must be an integer")
    return interactions


def validate_model(model):
    """Return every schema violation in model, as a list of strings."""
    errors = []
    if not isinstance(model, dict):
        return ["model: must be a JSON object"]
    _check_fields(model, TOP_FIELDS, "model", errors)
    components = _validate_components(model, errors)
    flows = _validate_flows(model, errors)
    component_ids = {
        c["id"] for c in components if isinstance(c, dict) and "id" in c
    }
    flow_ids = {f["id"] for f in flows if isinstance(f, dict) and "id" in f}
    _validate_interactions(model, errors, component_ids, flow_ids)
    return errors


def cmd_validate(args):
    model = load_model(args.model)
    errors = validate_model(model)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="check the model, write nothing")
    validate.add_argument("--model", required=True)
    validate.add_argument("--root", default=".")
    validate.set_defaults(func=cmd_validate)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ModelError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
