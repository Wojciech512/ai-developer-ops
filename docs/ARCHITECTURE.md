# Architektura ai-developer-ops

Repo-narzędzie: spec-driven, podwójnie recenzowany proces developerski dla dwóch
harnessów naraz — Claude Code (plugin) i Codex (skille + agenci TOML). Jedno źródło,
dwa kanały dystrybucji. Repo jest własnym marketplace'em Claude (`.claude-plugin/marketplace.json`,
`source: "./"`) i dogfooduje własny proces (patrz niżej).

## Stos

Czysty bash (`#!/usr/bin/env bash`, zgodny z bash 3.2 na macOS) + szablony
Markdown/JSON/TOML/YAML. Brak manifestu językowego (package.json, pyproject itd.).
Zależności runtime skryptów: `git`, `make`, `jq`, `npm`/`npx` oraz CLI:
`claude`, `codex`, `openspec`, `playwright-cli`. Testy: python `unittest` (stdlib,
bez zależności), uruchamiane przez `make test`.

## Punkty wejścia i przepływ sterowania

1. **`scripts/install.sh`** — raz na maszynę. Self-update (`git pull --ff-only`
   tylko przy czystym checkoucie), globalne npm (openspec, playwright-cli),
   instalacja/aktualizacja pluginów Claude (ai-developer-ops, superpowers,
   security-guidance, codex), symlinki: `templates/agents/*.md` → `~/.claude/agents`,
   `skills/*` → `~/.agents/skills`, `codex/agents/*.toml` → `~/.codex/agents`,
   Context7 MCP. Stan: `~/.ai-developer-ops-state/variant`.
2. **Skill `/ai-developer-ops:init`** → **`scripts/init.sh`** — raz na projekt.
   Deterministyczny scaffold: wykrywa wariant (`scripts/detect.sh`:
   claude | codex | claude-codex | none) i hosta z remote origin (github | gitlab | other),
   zapisuje je w `.aidevops/` (gitignored), kopiuje szablony przez `cp_if_absent`
   (nigdy nie nadpisuje plików użytkownika; wyjątek: handoff.md i evidence.md
   w `.aidevops/templates/` są odświeżane zawsze), ustawia `core.hooksPath=.githooks`.
   Część niedeterministyczną (wypełnienie TODO pod stack projektu) robi agent.
3. **Skille procesu** (`skills/{init,ops-feature,ops-critique,ops-review,ops-ship}/SKILL.md`)
   — właściwa logika workflow; `ops-feature` orkiestruje cykl życia zmiany
   z trzema bramkami ludzkimi (proposal, plan, merge). Czytają `.aidevops/variant`
   i `.aidevops/host` jako przełączniki.

## Przepływ danych

Źródłem prawdy zmiany jest `openspec/changes/<id>/` (proposal, specs, design,
tasks + handoff.md z ownerem i evidence.md z dowodami). Egzekwowanie bramki
`make check` w trzech punktach:

- **Hooki Claude** (`hooks/hooks.json` → `scripts/*.sh`): PreToolUse
  `protect-paths.sh` (blokuje edycje .env, lockfile'ów, migracji, CI; override
  `AIDEVOPS_ALLOW_PROTECTED=1`; fail-open bez jq), PostToolUse `format-file.sh`
  (uruchamia `make fmt-file FILE=...`, nigdy nie blokuje), Stop `stop-gate.sh`
  (blokuje koniec tury przy brudnym drzewie i czerwonym `make check`).
  Kontrakt hooków: exit 2 = block + stderr, exit 0 = przepuść.
- **`.githooks/pre-push`** — `make -s check` przed pushem.
- **CI** (`.github/workflows/ai-check.yml` / `templates/ci-gitlab.yml`) — `make check`.

## Układ katalogów

| Katalog | Rola |
|---|---|
| `scripts/` | Jedyna logika wykonywalna (install, init, detect, 3 hooki, format) |
| `skills/` | 5 skilli promptowych (wspólne dla Claude i Codex) |
| `templates/` | Pliki kopiowane przez init.sh do projektów (Makefile, AGENTS.md, CI, pre-push, PR/MR, settings.json) + `agents/docs-researcher.md` |
| `agents/` | `cross-reviewer.md` — recenzja B dla Claude |
| `codex/` | `config.snippet.toml` + `agents/*.toml` (explorer, worker, tester, reviewer, docs_researcher) |
| `hooks/` | `hooks.json` — podpięcie hooków pluginu |
| `tests/` | Testy charakteryzacyjne (detect, init, hooki) + `e2e_smoke.sh` |
| `.claude-plugin/` | Manifest pluginu i marketplace |
| `.aidevops/` | Generowany stan projektu (gitignored) |

## Dogfooding

Pliki w korzeniu — `Makefile`, `AGENTS.md`, `.githooks/`, `.github/`,
`.claude/settings.json`, `.codex/` — to wynik uruchomienia `scripts/init.sh`
na tym repo. Szablony w `templates/` pozostają generyczne (z TODO); kopie
w korzeniu są wypełnione pod ten stack. Zmiany wprowadzaj najpierw
w `templates/`, potem odśwież kopię.

## Bramki tego repo (`make check`)

- `lint` — shellcheck wszystkich skryptów (łącznie z pre-push).
- `typecheck` — `bash -n` skryptów, `jq empty` dla JSON, `tomllib` dla TOML.
- `test` — `python3 -m unittest discover -s tests` (kontrakty detect.sh, init.sh
  i hooków; PATH zawężony do stubów + `/usr/bin:/bin`, więc wariant i host są
  deterministyczne na macOS i na runnerze ubuntu).
- `make e2e` — pełny smoke init.sh w świeżym repo tymczasowym.

Konwencje: patrz `AGENTS.md`; proces i role modeli: `PROTOCOL.md`, `MODELS.md`.
