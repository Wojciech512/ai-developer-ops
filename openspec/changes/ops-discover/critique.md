# Critique: ops-discover

Krytyk: `codex exec -m gpt-6-astra -c model_reasoning_effort=high` (wariant claude-codex).
Wejście: proposal.md, design.md, specs/architecture-discovery/spec.md, tasks.md — skonkatenowane z numerami linii.
Data: 2026-10-28.

## critical

- **BLOCKER — Post-merge refresh loses the change scope.** `openspec/changes/ops-discover/design.md:76` calculates the diff against `main` after merge. On updated `main`, this compares `HEAD` with itself and returns nothing. Filtering to existing directories also excludes deleted directories—the exact locations needed to remove obsolete components. Capture the change’s base and changed paths before merge, including deletions, and define empty-scope behavior.

- **BLOCKER — The renderer cannot satisfy the empty-directory scenario.** `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:30–31` requires identical output when only the model is copied into an empty directory. `openspec/changes/ops-discover/design.md:66` requires referenced source paths to exist, while line 68 obtains metadata from Git and the current date. A normal model fails validation there; Markdown is not reproducible either. Separate filesystem validation from rendering and specify all rendering inputs explicitly.

- **BLOCKER — The aggregation algorithm contradicts its acceptance test.** `openspec/changes/ops-discover/design.md:60` collapses an entire layer and stops once the count is at most 12. With 14 components distributed across layers as 4/4/3/3, the first collapse produces **11** participants. `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:70` and `openspec/changes/ops-discover/tasks.md:15` require exactly 12. Change either the algorithm or the requirement; one convenient fixture cannot reconcile them.

- **BLOCKER — Manual preservation makes other mandatory guarantees impossible.** `openspec/changes/ops-discover/design.md:64` preserves arbitrary marked lines unchanged. A marked participant declaration can exceed the participant limit or lack a legend entry; a marked unlabelled arrow violates arrow validation; a marked declaration for a deleted component must both survive and disappear under `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:118–129`. Define allowed manual syntax and explicit precedence. Moving executable PlantUML into an “orphan” comment block does not disable it.

- **BLOCKER — Modification times cannot establish the promised source/image correspondence.** `openspec/changes/ops-discover/design.md:70` accepts any SVG whose timestamp is equal to or newer than the PUML timestamp. A checkout can give stale committed content equal timestamps or write the SVG later, so the scenario at `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:162–163` can pass incorrectly. Record and verify a source-content digest, or compare regenerated output. The equal-timestamp test currently institutionalizes a false negative.

## major

- **WARN — Renderer availability in consumer repositories is unspecified.** `openspec/changes/ops-discover/proposal.md:36` describes installing skill symlinks, while `openspec/changes/ops-discover/tasks.md:39` requires invoking `render_arch.py`. No task installs that script into consumer repositories or specifies how the skill resolves it from its installation directory. Add an installed-skill smoke test in a separate repository containing no ai-developer-ops scripts.

- **WARN — Scoped refresh has no defined reconciliation algorithm.** `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:133–139` protects outside components but says nothing about interactions, flows, renames, or components represented by parent directories. If an in-scope component disappears, an outside interaction may become dangling. If a flow crosses the boundary, restricted reading may prevent reconstructing it. Define ownership and merge rules for all model entities, plus behavior for scoped discovery without an existing model.

- **WARN — The claimed atomicity is not implemented by the proposed interface.** `openspec/changes/ops-discover/design.md:66` promises protection against a new PUML paired with old Markdown, but line 68 provides separate commands. PUML can succeed before Markdown fails because of permissions, Git metadata, or interruption. `openspec/changes/ops-discover/tasks.md:23` tests only rejection of an invalid model, not a write failure. Specify transactional generation or narrow the guarantee to individual files; include the model itself in the publication strategy.

- **WARN — Aggregation changes execution semantics.** `openspec/changes/ops-discover/design.md:60` deduplicates messages without considering their positions. A flow that performs the same operation twice loses its second occurrence. Grouping can also turn calls between separate components into self-calls. Preserve repeated execution steps and define how collapsed internal interactions are represented. Additionally, generated IDs such as `ServiceGroup` can collide with valid user-defined IDs; no reservation or collision rule exists.

- **WARN — The schema is not sufficiently defined to be “frozen.”** `openspec/changes/ops-discover/design.md:45–52` omits flow-ID uniqueness, validation of interaction flow references, allowed `kind` values beyond the narrative, and precise field types. `openspec/changes/ops-discover/tasks.md:8–9` does not cover these cases, zero main flows, or malformed `seq` values. A renderer could pass every listed validation test while silently omitting interactions assigned to nonexistent flows. Specify the complete schema and rejection behavior.

- **WARN — Manual preservation depends on unstable, nonunique section identities.** `openspec/changes/ops-discover/design.md:64` identifies groups by their labels, although the model permits multiple flows with the same label. It also sorts retained lines, which can reorder messages or break multi-line PlantUML constructs. Define stable section identifiers and whether manual additions are independent single lines or structured blocks.

- **WARN — End-to-end determinism remains an unsupported requirement.** `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:45–46` requires two discovery runs to produce identical PUML. `openspec/changes/ops-discover/design.md:82` explicitly acknowledges that discovery can rename the same service. Renderer sorting cannot stabilize component selection, labels, flow boundaries, or operation wording. A one-time successful comparison in `openspec/changes/ops-discover/tasks.md:53` does not establish the general requirement. Either narrow it to rendering identical models or define stable discovery identities and reconciliation.

- **WARN — Post-merge documentation changes have no delivery lifecycle.** `openspec/changes/ops-discover/tasks.md:65–66` ships and merges before generating refreshed documentation. Nothing assigns responsibility for committing, reviewing, checking, and publishing those subsequent changes. This can leave the merged repository stale and the local checkout dirty. Move refresh before shipping or explicitly define the follow-up change.

- **WARN — Output escaping is entirely unspecified.** `openspec/changes/ops-discover/design.md:31–40` accepts labels, operation names, and paths that become PlantUML or Markdown. Quotes, newlines, brackets, and other syntax characters can invalidate output or create unintended diagram statements. Define escaping or rejection rules and test hostile syntax as well as ordinary filenames containing spaces.

- **WARN — Task 6.1 hides most of the workflow implementation in one context.** `openspec/changes/ops-discover/tasks.md:39` combines orchestration, model synthesis, validation, refresh reconciliation, scope handling, rendering, and command discovery, then verifies only line count and frontmatter. Split these behaviors into separately verifiable tasks. The critical scoped-refresh behavior currently has no dedicated behavioral test or specified manual fixture.

## minor

- **NOTE — Early tasks depend on outputs created later.** `openspec/changes/ops-discover/tasks.md:7` requires a helper test to render successfully before the renderer exists. Its “minimal correct model” references the example at `openspec/changes/ops-discover/design.md:33–40`, which uses undeclared component `Developer`. Task 2.4 at `openspec/changes/ops-discover/tasks.md:16` checks the repository diagram before task 8.2 generates it. Use self-contained fixtures and correct the dependency order.

- **NOTE — Legend requirements disagree about actors and aggregation.** `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:104` requires one line per component with an existing path. `openspec/changes/ops-discover/tasks.md:21` requires one line per participant after aggregation and allows actors without paths. State the actor exception and distinguish original components from rendered participants.

- **NOTE — The Python gate is added inconsistently.** `openspec/changes/ops-discover/tasks.md:33–34` adds documentation targets to the template but describes Python compilation only when modifying the root copy. This leaves unclear whether initialized repositories receive the same gate and conflicts with treating templates as the source of truth.

- **NOTE — The date prohibition test rejects legitimate model content.** `openspec/changes/ops-discover/tasks.md:14` bans a year number or the word `date` anywhere in PUML. Operations such as `update`, an API named `DateService`, or a legitimate version label can trigger this without introducing runtime metadata. Test output stability under different clock values instead.

- **NOTE — Onboarding limits lack measurable or satisfiable boundaries.** `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:143` requires four pages without specifying rendering conditions, and exactly five execution paths even for a repository with fewer real paths. Define a measurable size budget and allow fewer paths when supported by the source.

## open questions

- **WARN — What happens when five concurrent agents are unavailable?** `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:11–16` mandates five parallel assignments in one turn. Is batching permitted under concurrency limits, and how are failed or unavailable agents handled?

- **WARN — How are existing consumer Makefiles upgraded?** `openspec/changes/ops-discover/tasks.md:33–34` updates the template and this repository’s copy. What delivers `docs` and `docs-fresh` to already initialized repositories without overwriting their custom commands?

- **WARN — What happens when a tool exists but cannot render?** `openspec/changes/ops-discover/design.md:72` covers absent executables, but not an unavailable Docker daemon, failed image pull, invalid PUML, or a renderer that leaves an old SVG behind. Which failures abort discovery, and when is a refresh reported as successful?

- **WARN — Does the architecture-update prohibition exempt discovery itself?** `openspec/changes/ops-discover/specs/architecture-discovery/spec.md:191–197` forbids updating the diagram during a task, while lines 175–187 require an automated update within the feature workflow. State the exception so agents do not receive conflicting instructions.

**Verdict: FAIL.**
