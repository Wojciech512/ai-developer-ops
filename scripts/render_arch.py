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
from pathlib import Path

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

# Rendered text reaches both PlantUML and Markdown, whose special characters
# differ. Rather than escape correctly for two grammars, allow one safe set
# and reject the rest: these values are short and authored, so "fix the model"
# is an unambiguous instruction. \w covers letters (diacritics included),
# digits and underscore.
TEXT_CHAR_RE = re.compile(r"[\w \-./():,]")
# Filesystems permit far more than the text fields do; only the two
# characters that would break a Markdown code span or a line survive as rules.
PATH_FORBIDDEN = ("`", "\n", "\r")


def _bad_text_chars(value):
    return sorted({c for c in value if not TEXT_CHAR_RE.fullmatch(c)})


def _validate_text(value, field, where, errors):
    """Reject empty, whitespace-only, and format-breaking text."""
    if not isinstance(value, str):
        errors.append(f"{where}: {field} {value!r} must be a string")
        return
    if not value.strip():
        errors.append(f"{where}: {field} must not be empty")
        return
    bad = _bad_text_chars(value)
    if bad:
        shown = " ".join(repr(c) for c in bad)
        errors.append(
            f"{where}: {field} {value!r} contains disallowed "
            f"character(s): {shown}"
        )


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


def _validate_components(model, errors, root):
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
        _validate_text(component["label"], "label", where, errors)
        _validate_component_path(component, where, root, errors)
    return components


def _validate_component_path(component, where, root, errors):
    """A path is required and must exist, except on the actor layer."""
    cid = component.get("id")
    path = component["path"]
    if component.get("layer") == "actor":
        if path is not None:
            errors.append(
                f"{where}: component {cid!r} is on the actor layer and must "
                f"have path null, got {path!r}"
            )
        return
    if path is None:
        errors.append(
            f"{where}: component {cid!r} is on layer "
            f"{component.get('layer')!r} and must declare a path"
        )
        return
    if not isinstance(path, str) or not path:
        errors.append(f"{where}: path {path!r} must be a non-empty string")
        return
    for char in PATH_FORBIDDEN:
        if char in path:
            errors.append(
                f"{where}: path {path!r} contains disallowed "
                f"character {char!r}"
            )
            return
    if root is not None and not (root / path).exists():
        errors.append(
            f"{where}: path {path!r} does not exist under {root}"
        )


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
        _validate_text(flow["label"], "label", where, errors)
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
        _validate_text(interaction["verb"], "verb", where, errors)
        _validate_text(interaction["op"], "op", where, errors)
        seq = interaction["seq"]
        # bool is a subclass of int; a true/false seq is a typo, not an order.
        if type(seq) is not int:
            errors.append(f"{where}: seq {seq!r} must be an integer")
    return interactions


def validate_model(model, root=None):
    """Return every schema violation in model, as a list of strings."""
    errors = []
    if not isinstance(model, dict):
        return ["model: must be a JSON object"]
    _check_fields(model, TOP_FIELDS, "model", errors)
    if "title" in model:
        _validate_text(model["title"], "title", "model", errors)
    components = _validate_components(model, errors, root)
    flows = _validate_flows(model, errors)
    component_ids = {
        c["id"] for c in components if isinstance(c, dict) and "id" in c
    }
    flow_ids = {f["id"] for f in flows if isinstance(f, dict) and "id" in f}
    _validate_interactions(model, errors, component_ids, flow_ids)
    return errors


LAYER_LABELS = {
    "actor": "aktor",
    "ui": "UI",
    "api": "API",
    "service": "serwisy",
    "repository": "repozytoria",
    "data": "dane",
    "integration": "integracje",
}


def _layer_index(layer):
    return LAYERS.index(layer)


def participants(model):
    """Components in render order: layer vocabulary, then id."""
    return sorted(
        model["components"],
        key=lambda c: (_layer_index(c["layer"]), c["id"]),
    )


def ordered_flows(model):
    """The single main flow first, then independent flows by id."""
    flows = model["flows"]
    main = [f for f in flows if f["kind"] == "main"]
    independent = sorted(
        (f for f in flows if f["kind"] != "main"), key=lambda f: f["id"]
    )
    return main + independent


def _message_key(interaction):
    # seq carries the sequence; the rest are tie-breakers so that two
    # messages sharing a seq never depend on their order in the file.
    return (
        interaction["seq"],
        interaction["from"],
        interaction["to"],
        interaction["verb"],
        interaction["op"],
    )


def flow_messages(model, flow_id):
    return sorted(
        (i for i in model["interactions"] if i["flow"] == flow_id),
        key=_message_key,
    )


def _declaration(component):
    keyword = "actor" if component["layer"] == "actor" else "participant"
    return f'{keyword} "{component["label"]}" as {component["id"]}'


def _message(interaction):
    label = f"{interaction['verb'].strip()} {interaction['op'].strip()}"
    return f"{interaction['from']} -> {interaction['to']} : {label}"


def render_puml(model):
    """Render the model to PlantUML text. Pure: no clock, no filesystem."""
    lines = ["@startuml", f"title {model['title']}", ""]

    by_layer = {}
    for component in participants(model):
        by_layer.setdefault(component["layer"], []).append(component)
    for layer in LAYERS:
        members = by_layer.get(layer)
        if not members:
            continue
        lines.append(f'box "{LAYER_LABELS[layer]}"')
        # Anchor on the canonical layer key, not the display label: manual
        # additions are re-attached by this marker, which never changes.
        lines.append(f"' layer:{layer}")
        lines.extend(_declaration(c) for c in members)
        lines.append("end box")
        lines.append("")

    flows = ordered_flows(model)
    for flow in flows:
        messages = flow_messages(model, flow["id"])
        if flow["kind"] == "main":
            lines.extend(_message(m) for m in messages)
            lines.append("")
            continue
        lines.append(f"group {flow['label']}")
        lines.append(f"' flow:{flow['id']}")
        lines.extend(_message(m) for m in messages)
        lines.append("end")
        lines.append("")

    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def _validated(args):
    """Load and validate, or raise ModelError carrying every violation."""
    model = load_model(args.model)
    errors = validate_model(model, Path(args.root))
    if errors:
        raise ModelError("\n".join(errors))
    return model


def _write_atomic(path, text):
    """Write via a sibling temp file then replace, so no reader sees a
    half-written document."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def cmd_puml(args):
    model = _validated(args)
    _write_atomic(args.out, render_puml(model))
    return 0


def cmd_validate(args):
    model = load_model(args.model)
    errors = validate_model(model, Path(args.root))
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

    puml = sub.add_parser("puml", help="render the PlantUML diagram")
    puml.add_argument("--model", required=True)
    puml.add_argument("--out", required=True)
    puml.add_argument("--root", default=".")
    puml.set_defaults(func=cmd_puml)

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
