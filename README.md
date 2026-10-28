# ai-developer-ops

Jeden proces tworzenia oprogramowania z agentami AI. Działa z samym Claude Code, samym Codex albo oboma. Wariant jest wykrywany, nie wybierany.

To repo jest pluginem Claude Code (`.claude-plugin/`) i paczką skilli w standardzie SKILL.md, którą czyta Codex. Jedno repo, jedno źródło.

## Stos
- Spec: OpenSpec (`/opsx:explore`, `/opsx:propose`, `/opsx:apply`, `/opsx:verify`, `/opsx:archive`)
- Wykonanie: Superpowers (TDD, świeży subagent na zadanie, dwustopniowy review) w Claude; subagenci TOML w Codex
- Review: `/code-review` (Claude), `codex review` (Codex), `/codex:adversarial-review` (plugin OpenAI, gdy są oba)
- E2E: playwright-cli + Playwright Test
- Security: plugin security Anthropic, Codex Security plugin
- Nasze spoiwo: 5 skilli, 1 agent Claude, 4 agentów Codex, 3 hooki, szablony

## Instalacja raz na komputer
    git clone https://github.com/Wojciech512/ai-developer-ops ~/.ai-developer-ops
    ~/.ai-developer-ops/scripts/install.sh

## Inicjalizacja projektu
    git clone <projekt> && cd <projekt>
    claude   ->  /ai-developer-ops:init        (Codex: codex -> $init)

## Proces
spec (OpenSpec) -> plan i tasks -> wykonanie w harnessie, jedno zadanie na świeży kontekst -> `make check` w hookach -> review (spec, poprawność, security, drugi model) -> PR/MR. Człowiek decyduje trzy razy: propose, plan, merge.

## Ściągawka według sytuacji

| Sytuacja | Wypisujesz | Co się dzieje pod spodem |
|---|---|---|
| Zmiana większa niż jedno zdanie | `/ai-developer-ops:ops-feature <id> "<cel>"` | OpenSpec propose -> `ops-critique` -> `using-git-worktrees` + `subagent-driven-development` + TDD -> `ops-review` -> `ops-ship` |
| Bug | `/superpowers:systematic-debugging`, potem `/ai-developer-ops:ops-review <zakres fiksa>` | test odtwarzający -> przyczyna -> fix; cztery etapy review. `HEAD~1..HEAD` dopiero gdy cały fix siedzi w ostatnim commicie |
| Review czegokolwiek (PR, MR, gałąź, ścieżka) | `/ai-developer-ops:ops-review <target>` | `/code-review`, security, drugi model |
| Poprawka na jedno zdanie | zwykła prośba | hooki i `make check` pilnują; TDD z `AGENTS.md` odpala się samo |
| PR/MR | `/ai-developer-ops:ops-ship <id>` | warunki wstępne, szablon, dowody, boty |
| Pytanie o API biblioteki | `@agent-docs-researcher <pytanie>` | Context7 w subagencie |

**Czego nie mieszać.** Jeden plan i tylko jeden: `openspec/changes/<id>/tasks.md` — `superpowers:brainstorming` i `superpowers:writing-plans` odpalaj wyłącznie ręcznie, żeby nie powstał drugi plan, a zmianę prowadzoną przez OpenSpec zamykaj przez `ops-ship`, nie przez `superpowers:finishing-a-development-branch`. Bug zostaje bugiem nawet gdy fix ma jedną linię: test odtwarzający jest obowiązkowy.

**W Codex nie ma Superpowers.** Proces niosą skille `ops-*` z agentami TOML (`worker`, `reviewer`, `tester`, `explorer`, `docs_researcher`), wywołania to `$ops-feature`, `$ops-review`, `$ops-ship`. Zamiast `systematic-debugging` regułę buga niesie `AGENTS.md` (najpierw test odtwarzający) plus agent `tester`, a agent od dokumentacji nazywa się `docs_researcher` z podkreśleniem.

## Pliki
- `PROTOCOL.md` komunikacja Claude Code <-> Codex
- `MODELS.md` model per etap
- `LINKS.md` źródła
- `skills/` init, review, feature, plan-critique, ship
- `scripts/` install.sh (maszyna), init.sh (projekt), hooki bramek
- `templates/` AGENTS.md, Makefile, CI, PR/MR template
