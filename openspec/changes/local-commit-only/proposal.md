# Proposal

## Why

Agent może dziś wypchnąć cokolwiek na `origin` i nic go nie zatrzymuje. `.claude/settings.json` ma `"Bash(git *)"` na liście `allow`, a w `deny` tylko `git push --force*` i `git push -f*` — więc `git push origin HEAD:main` jest autoryzowany automatycznie, bez promptu. Zdarzyło się to realnie 2026-10-28: przy zmianie `docs-cheatsheet` agent trzykrotnie wypchnął na `origin/main` (dwa fast-forwardy i commit archiwizacyjny). Każdy push był poprzedzony pytaniem, które użytkownik zatwierdził, ale pytanie nie zastępuje bramki — push na domyślną gałąź jest akcją zewnętrzną i praktycznie nieodwracalną.

Dodatkowo `skills/ops-ship/SKILL.md:8` wprost **instruuje** agenta, żeby zrobił `git push -u origin <branch>`. Reguła i skill są więc dziś w sprzeczności.

Oczekiwany stan: wynikiem pracy agenta w worktree jest **commit w lokalnym repozytorium**. Push, PR/MR i merge na zdalnym to czynności człowieka.

## What Changes

- **BREAKING** dla `ops-ship`: skill przestaje pushować i otwierać PR/MR. Zamiast tego weryfikuje warunki wstępne, przygotowuje commit i wypełnione ciało PR/MR do pliku, a na końcu wypisuje człowiekowi dokładne komendy do uruchomienia. Opis skilla w frontmatterze przestaje obiecywać "Commit, push, open a PR".
- Nowy hook `scripts/deny-push.sh` (PreToolUse na `Bash`): `exit 2` dla operacji przenoszących kod na zdalne — `git push` (dowolne zdalne, także podane jako URL), `gh pr create|merge`, `gh release create`, `glab mr create|merge` oraz `gh api` z metodą zapisującą poza jawną listą dozwolonych ścieżek. Hook czyta całą komendę, więc łapie formy, których wzorzec uprawnień nie widzi: `git -C <ścieżka> push`, push za `&&` lub `;`, push z flagami. Zabroniona komenda występująca jako **tekst w argumencie** przechodzi — inaczej bramka blokowałaby przygotowanie materiałów dla człowieka.
- Rozszerzenie `scripts/protect-paths.sh`: pliki samej bramki (`scripts/deny-push.sh`, `hooks/hooks.json`, oba `settings.json`) stają się ścieżkami chronionymi. Bez tego bramkę wyłącza jedna edycja.
- `hooks/hooks.json`: rejestracja hooka z matcherem `Bash`.
- `templates/settings.json` i `.claude/settings.json`: wpisy `deny` jako druga warstwa (deny ma pierwszeństwo nad allow i obowiązuje też podagentów, które nie dziedziczą hooków sesji w ten sam sposób).
- `templates/AGENTS.md` i `AGENTS.md`: reguła prozą, bo Codex czyta AGENTS.md natywnie i nie widzi hooków Claude Code. Bez tego wariant `codex` nie jest objęty zakazem.
- `AGENTS.md` i `templates/AGENTS.md`: Definition of Done rozdzielone na część agenta (zielona bramka, review bez BLOCKER-a, `evidence.md`, zgodny spec, przygotowana treść PR/MR, lokalny commit) i część człowieka (otwarcie PR/MR). Dziś punkt 5 wymaga "PR/MR z szablonu", czego agent po tej zmianie nie może zrobić — repo wymagałoby rzeczy zabronionej.
- `templates/handoff.md`: nowy status `ready-to-push`.
- `AGENTS.md` i `templates/AGENTS.md`, sekcja `## Konwencje`: zakaz trailerów atrybucji AI (`Co-Authored-By: Claude ...`) w commitach i w treści PR/MR. Rozszerzenie zakresu zgłoszone przez użytkownika w trakcie implementacji; mieści się w tej samej kategorii co zakaz zapisu na zdalne (co agentowi wolno), dlatego trafia tutaj, a nie do osobnej zmiany.
- `tests/test_hooks.py`: charakteryzacja nowego hooka, w tym przypadki niewinne (commit z opisem wspominającym push, `git log --grep=push`, zapis instrukcji do pliku) i kontrakt niemożności oceny.
- `tests/e2e_smoke.sh`: asercje, że świeżo zainicjalizowany projekt dostaje regułę i wpisy `deny` — wykonywane **przed** `trap rm -rf`, bo inaczej nie ma czego sprawdzać.

Czego **nie** zmieniamy: `.githooks/pre-push` zostaje (bramka `make check` przy pushu człowieka). `git commit` pozostaje dozwolony — commit jest oczekiwanym wynikiem. Komentarze na istniejącym PR/MR pozostają dozwolone (decyzja użytkownika: zakaz dotyczy operacji przenoszących kod), więc `skills/ops-review/SKILL.md:12` z `--comment` i prośba o review botów w `ops-ship` zostają bez zmian.

**To nie jest sandbox.** Agent, który celowo chce obejść bramkę, zrobi to skryptem, `curl`-em albo narzędziem MCP. Bramka zatrzymuje domyślną ścieżkę, nie przeciwnika. Model zagrożeń wybrany przez użytkownika po przedstawieniu twardszej alternatywy; spec nie obiecuje więcej, niż bramka daje.

## Capabilities

### New Capabilities
- `agent-guardrails`: co agentowi wolno, a czego nie wolno zrobić w repozytorium — wymuszane mechanicznie, nie tylko opisane. Ta zmiana wnosi pierwsze wymagania: zakaz zapisu na zdalne i commit lokalny jako koniec pracy agenta. Granica jest celowo wybrana tak, żeby mogła później przyjąć wymagania dla istniejących bramek (`protect-paths`, `stop-gate`), których dziś żaden spec nie opisuje. Nie dopisujemy ich w tej zmianie — nie wymyślamy wymagań dla kodu, którego nie ruszamy.

### Modified Capabilities
Brak. Projekt nie ma jeszcze żadnego speca (`openspec list --specs` → "No specs found"), więc nie ma czego modyfikować.

## Impact

- Pliki: `scripts/deny-push.sh` (nowy), `scripts/protect-paths.sh`, `hooks/hooks.json`, `.claude/settings.json`, `templates/settings.json`, `AGENTS.md`, `templates/AGENTS.md`, `templates/handoff.md`, `.aidevops/templates/handoff.md`, `skills/ops-ship/SKILL.md`, `tests/test_hooks.py`, `tests/e2e_smoke.sh`.
- Konwencja z `AGENTS.md`: `templates/` jest źródłem prawdy, a `AGENTS.md`/`settings.json` w korzeniu to kopie z `init.sh`. Każdą zmianę wprowadzamy najpierw w `templates/`, potem odświeżamy kopię.
- Ryzyko numer jeden: hook może zablokować **człowieka**, jeśli PreToolUse odpala się także dla komend wpisywanych z prefiksem `!`. Nie wiem tego i nie zgaduję — rozstrzyga to zadanie w planie, empirycznie, przed dopięciem hooka. Jeśli blokuje człowieka, hook musi rozróżniać wywołanie agenta od wywołania użytkownika albo zostaje tylko warstwa `deny` plus reguła w AGENTS.md.
- Ryzyko: `deny` na `Bash(gh *)` byłoby zbyt szerokie i zabiłoby `gh api --method POST /markdown`, który ta zmiana i poprzednia (`docs-cheatsheet`) używają jako dowodu renderu. Wzorce muszą być chirurgiczne i pokryte testem.
- Bramki: `make check` (shellcheck na nowym skrypcie, `bash -n`, `jq` na `hooks.json` i `settings.json`, unittest) oraz `make e2e`.
- Dowód końcowy tej zmiany to commit na `feat/local-commit-only` w lokalnym repo. Nic nie trafia na `origin` — zgodnie z regułą, którą ta zmiana wprowadza.
