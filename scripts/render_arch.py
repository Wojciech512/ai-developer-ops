#!/usr/bin/env python3
"""Render docs/architecture.{puml,md} from docs/architecture.model.json.

The renderer is a pure function of the model: it validates and formats, it
never analyses project code. See openspec/changes/ops-discover/design.md
for the frozen schema and the ordering, aggregation and preservation rules.
"""
import argparse
import datetime
import json
import re
import subprocess
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


MAX_PARTICIPANTS = 12


def aggregate(components):
    """Collapse whole layers until at most MAX_PARTICIPANTS remain.

    Returns (participants, mapping). Each participant carries `covers`: the
    original components it stands for, so the legend can list every path
    without re-deriving it. mapping sends an original id to its rendered id.

    Collapsing a whole layer overshoots the limit (14 components laid out
    4/4/3/3 land on 11), which is why the limit is a ceiling rather than an
    exact count. The layer chosen is the fullest one; ties go to the layer
    later in LAYERS, because overflow is usually integrations.
    """
    buckets = {}
    for component in components:
        buckets.setdefault(component["layer"], []).append(component)
    collapsed = set()

    def total():
        return sum(
            1 if layer in collapsed else len(members)
            for layer, members in buckets.items()
        )

    while total() > MAX_PARTICIPANTS:
        candidates = [
            (len(members), _layer_index(layer), layer)
            for layer, members in buckets.items()
            if layer not in collapsed and len(members) > 1
        ]
        if not candidates:
            break
        candidates.sort()
        collapsed.add(candidates[-1][2])

    participants = []
    mapping = {}
    for layer in LAYERS:
        members = sorted(buckets.get(layer, []), key=lambda c: c["id"])
        if not members:
            continue
        if layer in collapsed:
            aggregate_id = f"{layer.capitalize()}{AGGREGATE_SUFFIX}"
            participants.append({
                "id": aggregate_id,
                "label": f"{LAYER_LABELS[layer]} ({len(members)})",
                "layer": layer,
                "covers": members,
            })
            for member in members:
                mapping[member["id"]] = aggregate_id
            continue
        for member in members:
            participants.append({
                "id": member["id"],
                "label": member["label"],
                "layer": layer,
                "covers": [member],
            })
            mapping[member["id"]] = member["id"]
    return participants, mapping


def _dedupe_adjacent(messages):
    """Drop a message identical to the one immediately before it.

    Only adjacent duplicates: a flow that performs the same operation twice,
    separated by another message, keeps both occurrences.
    """
    kept = []
    for message in messages:
        if kept and kept[-1] == message:
            continue
        kept.append(message)
    return kept


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


def _declaration(participant):
    keyword = "actor" if participant["layer"] == "actor" else "participant"
    return f'{keyword} "{participant["label"]}" as {participant["id"]}'


def _message(interaction, mapping):
    label = f"{interaction['verb'].strip()} {interaction['op'].strip()}"
    source = mapping[interaction["from"]]
    target = mapping[interaction["to"]]
    return f"{source} -> {target} : {label}"


def _rendered_messages(model, flow_id, mapping):
    """Messages of one flow, in order, with aggregates applied.

    An interaction whose two ends collapsed into the same aggregate becomes
    a self-message rather than disappearing: dropping it would change the
    number of steps the flow performs.
    """
    ordered = flow_messages(model, flow_id)
    return _dedupe_adjacent([_message(m, mapping) for m in ordered])


def render_puml(model, manual=()):
    """Render the model to PlantUML text. Pure: no clock, no filesystem."""
    rendered, mapping = aggregate(participants(model))
    rendered_ids = {p["id"] for p in rendered}
    flows = ordered_flows(model)
    buckets, orphans = _partition_manual(
        manual,
        rendered_ids,
        {p["layer"] for p in rendered},
        {f["id"] for f in flows},
    )

    def manual_for(section):
        return [e.live_line() for e in buckets.get(section, [])]

    lines = ["@startuml", f"title {model['title']}", ""]

    by_layer = {}
    for participant in rendered:
        by_layer.setdefault(participant["layer"], []).append(participant)
    for layer in LAYERS:
        members = by_layer.get(layer)
        if not members:
            continue
        lines.append(f'box "{LAYER_LABELS[layer]}"')
        # Anchor on the canonical layer key, not the display label: manual
        # additions are re-attached by this marker, which never changes.
        lines.append(f"' layer:{layer}")
        lines.extend(_declaration(p) for p in members)
        lines.extend(manual_for(("layer", layer)))
        lines.append("end box")
        lines.append("")

    for flow in flows:
        messages = _rendered_messages(model, flow["id"], mapping)
        if flow["kind"] == "main":
            lines.extend(messages)
            lines.extend(manual_for(("body", None)))
            lines.append("")
            continue
        lines.append(f"group {flow['label']}")
        lines.append(f"' flow:{flow['id']}")
        lines.extend(messages)
        lines.extend(manual_for(("flow", flow["id"])))
        lines.append("end")
        lines.append("")

    if orphans:
        # Commented out on purpose: a live message naming a participant that
        # no longer exists would make PlantUML invent one, pushing past the
        # participant limit and past the legend.
        lines.extend(e.orphan_line() for e in orphans)
        lines.append("")

    lines.append("@enduml")
    return "\n".join(lines) + "\n"


# A manual addition is marked by a trailing comment. Orphans keep a distinct
# marker so a disabled line stays recognisable across refreshes instead of
# being re-commented every run.
MANUAL_MARKER = "' manual"
ORPHAN_MARKER = "' manual-orphan"

# Manual additions may not restructure the diagram: a declaration could push
# past the participant limit or slip past the legend, and an activation could
# unbalance the file.
MANUAL_FORBIDDEN = (
    "participant", "actor", "box", "end box", "group", "end",
    "activate", "deactivate", "@startuml", "@enduml",
)
MANUAL_ALLOWED = (
    "a message (A -> B : text, A --> B : text), "
    "a note (note left of X : text, note right of X : text), "
    "or a full-line comment ('...)"
)

MANUAL_MESSAGE_RE = re.compile(r"^(\w+)\s*-{1,2}>\s*(\w+)\s*:\s*\S")
MANUAL_NOTE_RE = re.compile(r"^note\s+(?:left|right)\s+of\s+(\w+)\s*:\s*\S")


class ManualLine:
    """A manual addition, its section, and the ids it refers to."""

    def __init__(self, content, section, orphaned):
        self.content = content
        self.section = section
        self.orphaned = orphaned

    def references(self):
        message = MANUAL_MESSAGE_RE.match(self.content)
        if message:
            return [message.group(1), message.group(2)]
        note = MANUAL_NOTE_RE.match(self.content)
        if note:
            return [note.group(1)]
        return []

    def live_line(self):
        return f"{self.content} {MANUAL_MARKER}"

    def orphan_line(self):
        return f"' {self.content} {ORPHAN_MARKER}"


def _manual_content(line):
    """Return (content, orphaned) for a manual line, or None."""
    stripped = line.strip()
    if stripped.endswith(ORPHAN_MARKER):
        content = stripped[: -len(ORPHAN_MARKER)].rstrip()
        # Orphans are stored commented out; drop that leading marker.
        if content.startswith("'"):
            content = content[1:].strip()
        return content, True
    if stripped.endswith(MANUAL_MARKER):
        return stripped[: -len(MANUAL_MARKER)].rstrip(), False
    return None


def parse_manual(text):
    """Collect manual lines from an existing .puml with their sections.

    Sections are identified by the ' layer:<layer> and ' flow:<id> anchors
    the renderer emits, never by display labels: a label can change while
    the anchor cannot.
    """
    manual = []
    section = ("body", None)
    for line in text.splitlines():
        stripped = line.strip()
        parsed = _manual_content(line)
        if parsed is not None:
            content, orphaned = parsed
            if content:
                manual.append(ManualLine(content, section, orphaned))
            continue
        if stripped.startswith("' layer:"):
            section = ("layer", stripped[len("' layer:"):])
        elif stripped.startswith("' flow:"):
            section = ("flow", stripped[len("' flow:"):])
        elif stripped in ("end box", "end"):
            section = ("body", None)
    return manual


def validate_manual(manual):
    """Return every manual line that breaks the closed syntax."""
    errors = []
    for entry in manual:
        if entry.orphaned:
            # Already disabled; its text is carried, not executed.
            continue
        content = entry.content
        head = content.split()[0] if content.split() else ""
        two = " ".join(content.split()[:2])
        if head in MANUAL_FORBIDDEN or two in MANUAL_FORBIDDEN:
            errors.append(
                f"manual line {content!r} starts with {head!r}, which may "
                f"not be added by hand; allowed: {MANUAL_ALLOWED}"
            )
            continue
        if content.startswith("'"):
            continue
        if MANUAL_MESSAGE_RE.match(content) or MANUAL_NOTE_RE.match(content):
            continue
        errors.append(
            f"manual line {content!r} is not one of: {MANUAL_ALLOWED}"
        )
    return errors


def _partition_manual(manual, rendered_ids, layers, flow_ids):
    """Split manual lines into per-section buckets plus orphans."""
    buckets = {}
    orphans = []
    for entry in manual:
        kind, key = entry.section
        unknown_refs = [
            ref for ref in entry.references() if ref not in rendered_ids
        ]
        homeless = (
            entry.orphaned
            or (kind == "layer" and key not in layers)
            or (kind == "flow" and key not in flow_ids)
        )
        if homeless or unknown_refs:
            orphans.append(entry)
            continue
        buckets.setdefault(entry.section, []).append(entry)
    for lines in buckets.values():
        lines.sort(key=lambda e: e.content)
    orphans.sort(key=lambda e: e.content)
    return buckets, orphans


SVG_NAME = "architecture.svg"
IMAGE_ALT = "Diagram sekwencji"
# The actor has no file; its legend entry says where the flow enters instead.
ACTOR_LEGEND = "wejście użytkownika"


def legend_entries(model):
    """One (label, description) per rendered participant, in render order.

    An aggregate lists every path it covers, so collapsing a layer hides
    participants from the diagram but never hides files from the legend.
    """
    rendered, _ = aggregate(participants(model))
    entries = []
    for participant in rendered:
        covered = participant["covers"]
        if participant["layer"] == "actor":
            entries.append((participant["label"], ACTOR_LEGEND))
            continue
        paths = sorted(c["path"] for c in covered)
        entries.append(
            (participant["label"], ", ".join(f"`{p}`" for p in paths))
        )
    return entries


def render_md(model, scope, date, commit):
    """Render ARCHITECTURE.md: title, image, legend, last update. No more."""
    lines = [
        f"# Architektura {model['title']}",
        "",
        f"![{IMAGE_ALT}]({SVG_NAME})",
        "",
        "## Legenda uczestników",
        "",
    ]
    for label, description in legend_entries(model):
        lines.append(f"- **{label}** — {description}")
    lines += [
        "",
        "## Ostatnia aktualizacja",
        "",
        f"- Data: {date}",
        f"- Zakres: {scope}",
        f"- Commit: `{commit}`",
        "",
    ]
    return "\n".join(lines)


def _today():
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def _head_commit():
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise ModelError(
            "could not read the HEAD commit; pass --commit explicitly"
        )
    return result.stdout.strip()


def _manual_or_empty(preserve):
    """Parse manual additions without raising, for validate's error list."""
    if not preserve:
        return []
    path = Path(preserve)
    if not path.exists():
        return []
    return parse_manual(path.read_text(encoding="utf-8"))


def _load_manual(preserve):
    """Read manual additions from an existing diagram, if there is one."""
    if not preserve:
        return []
    path = Path(preserve)
    if not path.exists():
        return []
    manual = parse_manual(path.read_text(encoding="utf-8"))
    errors = validate_manual(manual)
    if errors:
        raise ModelError("\n".join(errors))
    return manual


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
    manual = _load_manual(args.preserve)
    _write_atomic(args.out, render_puml(model, manual))
    return 0


def cmd_md(args):
    model = _validated(args)
    date = args.date or _today()
    commit = args.commit or _head_commit()
    _write_atomic(args.out, render_md(model, args.scope, date, commit))
    return 0


def cmd_all(args):
    """Render both documents, then write both.

    Validation, git metadata and both renders all happen before the first
    write, so a failure cannot leave a new diagram beside a stale document.
    What remains is the gap between two rename calls, not between two
    renders.
    """
    model = _validated(args)
    date = args.date or _today()
    commit = args.commit or _head_commit()
    manual = _load_manual(args.preserve)
    puml_text = render_puml(model, manual)
    md_text = render_md(model, args.scope, date, commit)
    _write_atomic(args.puml_out, puml_text)
    _write_atomic(args.md_out, md_text)
    return 0


def cmd_validate(args):
    model = load_model(args.model)
    errors = validate_model(model, Path(args.root))
    errors += validate_manual(_manual_or_empty(args.preserve))
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
    validate.add_argument("--preserve")
    validate.set_defaults(func=cmd_validate)

    puml = sub.add_parser("puml", help="render the PlantUML diagram")
    puml.add_argument("--model", required=True)
    puml.add_argument("--out", required=True)
    puml.add_argument("--root", default=".")
    puml.add_argument("--preserve")
    puml.set_defaults(func=cmd_puml)

    md = sub.add_parser("md", help="render the Markdown document")
    md.add_argument("--model", required=True)
    md.add_argument("--out", required=True)
    md.add_argument("--scope", required=True)
    md.add_argument("--date")
    md.add_argument("--commit")
    md.add_argument("--root", default=".")
    md.set_defaults(func=cmd_md)

    every = sub.add_parser("all", help="render both documents together")
    every.add_argument("--model", required=True)
    every.add_argument("--puml-out", required=True)
    every.add_argument("--md-out", required=True)
    every.add_argument("--scope", required=True)
    every.add_argument("--date")
    every.add_argument("--commit")
    every.add_argument("--root", default=".")
    every.add_argument("--preserve")
    every.set_defaults(func=cmd_all)

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
