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
    claude   ->  /init-ai-developer-ops        (Codex: codex -> $init-ai-developer-ops)

## Proces
spec (OpenSpec) -> plan i tasks -> wykonanie w harnessie, jedno zadanie na świeży kontekst -> `make check` w hookach -> review (spec, poprawność, security, drugi model) -> PR/MR. Człowiek decyduje trzy razy: propose, plan, merge.

## Pliki
- `PROTOCOL.md` komunikacja Claude Code <-> Codex
- `MODELS.md` model per etap
- `LINKS.md` źródła
- `skills/` init, review, feature, plan-critique, ship
- `scripts/` install.sh (maszyna), init.sh (projekt), hooki bramek
- `templates/` AGENTS.md, Makefile, CI, PR/MR template
