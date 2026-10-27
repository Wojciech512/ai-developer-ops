# Protokół współpracy Claude Code <-> Codex

## Źródło prawdy
Git + folder `openspec/changes/<id>/` (proposal.md, specs/, design.md, tasks.md z OpenSpec).
Nasze pliki w tym samym folderze: handoff.md (owner, status, next_action, blockers), evidence.md (wyniki `make check`, e2e, screenshoty), review-claude.md, review-codex.md.

## Reguły
1. Jeden pisarz na gałąź. Kod edytuje tylko narzędzie wpisane jako `owner` w handoff.md. Drugie czyta i pisze tylko do review-*.md.
2. Każda sesja zaczyna od handoff.md i tasks.md. Każda sesja kończy aktualizacją handoff.md.
3. Zmiana ownera = commit `handoff: claude -> codex` (lub odwrotnie).
4. Reviewer nigdy nie naprawia. Raportuje. Naprawia owner.
5. PR/MR jest kanałem asynchronicznym. Boty review komentują. Owner odpowiada i poprawia.

## Kanały
A. Pliki (zawsze): openspec/changes/<id>/.
B. Plugin OpenAI w Claude Code (gdy są oba): /codex:review --base <ref>, /codex:adversarial-review --base <ref>, /codex:rescue <zadanie>.
C. CLI (zapasowo): Claude -> Codex: codex exec -m gpt-6-astra "<prompt>"; Codex -> Claude: claude -p "<prompt>" --model opus --permission-mode dontAsk --allowedTools "Read,Grep,Glob,Bash(git diff *)".
D. MCP (opcjonalnie): claude mcp add codex -- codex mcp-server; codex mcp add claude -- claude mcp serve.
E. GitHub/GitLab: /code-review <PR|MR> --comment (Claude, oba hosty); @codex review (GitHub); Claude Code Review jako usługa (tylko GitHub).

## Role per wykryty wariant
- Tylko Claude: spec, plan, implementacja, review A (/code-review), review B (agent cross-reviewer na innym modelu).
- Tylko Codex: spec, plan, implementacja (worker), review A (codex review), review B (agent reviewer TOML na astra).
- Oba: Claude prowadzi; Codex robi review B (/codex:adversarial-review), zadania w tle (/codex:rescue, Codex Cloud, Automations).
