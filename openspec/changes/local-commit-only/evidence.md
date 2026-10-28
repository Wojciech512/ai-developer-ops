# Evidence: local-commit-only

## baseline (zadanie 0.1)
```
$ git rev-parse HEAD
bebc607d69bf143054e65b19aae1728812c72ed8

$ git ls-files --others --exclude-standard
openspec/changes/local-commit-only/.openspec.yaml
openspec/changes/local-commit-only/critique.md
openspec/changes/local-commit-only/design.md
openspec/changes/local-commit-only/evidence.md
openspec/changes/local-commit-only/handoff.md
openspec/changes/local-commit-only/proposal.md
openspec/changes/local-commit-only/specs/agent-guardrails/spec.md
openspec/changes/local-commit-only/tasks.md
```

## zadanie 1.1 — probe `!` vs PreToolUse: NIEROZSTRZYGNIĘTE

Ustalenie wstępne, istotne dla całego planu: `~/.ai-developer-ops` jest symlinkiem do
**głównego checkoutu**, nie do tego worktree:
```
$ readlink ~/.ai-developer-ops
/Users/wojciechwylezol/PycharmProjects/ai-developer-ops
```
Czyli `$CLAUDE_PLUGIN_ROOT` wskazuje główny checkout. Edycja `hooks/hooks.json` w tym
worktree **nie ma żadnego wpływu na bieżącą sesję**. Zadania 1.1 i 3.2 zakładały hook
działający na żywo, co z worktree jest nieosiągalne przez plugin.

Obejście: dokumentacja hooków mówi "Direct edits to hooks in settings files are normally
picked up automatically by the file watcher", więc probe zarejestrowano w
`.claude/settings.json` **tego worktree** (ustawienia projektowe dla cwd), bez dotykania
głównego checkoutu ani konfiguracji użytkownika.

Probe: `PreToolUse` / matcher `Bash` / komenda logująca `.tool_input.command` do
`/tmp/hook-probe.log` i zawsze `exit 0`.

**Kontrola dodatnia nie przeszła.** Po wykonaniu przez agenta `echo HOOK_PROBE_AGENT`
oraz, po 5 sekundach, `echo HOOK_PROBE_AGENT_2`:
```
$ ls -l /tmp/hook-probe.log
ls: /tmp/hook-probe.log: No such file or directory

$ jq -e '.hooks.PreToolUse[0].matcher' .claude/settings.json
"Bash"
```
JSON był poprawny, matcher ustawiony, a hook nie odpalił się nawet dla komendy agenta.
Najbardziej prawdopodobna przyczyna: Claude Code wymaga przeglądu/zatwierdzenia nowo
dodanych hooków przez człowieka, zanim zaczną obowiązywać (zabezpieczenie).

**Wniosek: wynik nierozstrzygnięty, nie negatywny.** Nie wiem, czy `PreToolUse` widzi
komendy wpisywane przez człowieka z prefiksem `!`. Dokumentacja
(`code.claude.com/docs/en/hooks.md`) tego nie precyzuje — pobrana i sprawdzona.

Dlaczego to ma znaczenie: bez kontroli dodatniej pusty log odczytałbym jako „hook nie
widzi komend człowieka", czyli dokładnie fałszywie negatywny wynik, przed którym
ostrzegał `critique.md` WARN 7. Kontrola dodatnia zarobiła tu na siebie.

Probe wycofany: `git diff --stat .claude/settings.json` jest pusty.

Konsekwencja dla planu: zadanie 3.1 (uzbrojenie bramki przez rejestrację w
`hooks/hooks.json`) **wstrzymane** do rozstrzygnięcia 1.1, zgodnie z warunkiem z
zadania 1.2. Pozostałe grupy (2, 4, 5, 6, 7, 8) są niezależne i wykonane.

## zadanie 7 — ops-ship przygotowuje, nie wykonuje

`skills/ops-ship/SKILL.md` przepisany: frontmatter nie obiecuje pushu/otwarcia PR jako
czynności skilla, kroki piszą `pr-body.md` i `handoff.md` (status=ready-to-push,
owner=human) **przed** commitem, krok review botów na istniejącym PR/MR zostaje, a
ostatni krok wypisuje człowiekowi gotowe komendy.

Weryfikacja (grep z zadania 7):
```
$ grep -n 'git push\|pr create\|mr create' skills/ops-ship/SKILL.md
15:   git push -u origin <branch>
16:   gh pr create --body-file openspec/changes/<id>/pr-body.md        # github
17:   glab mr create --description-file openspec/changes/<id>/pr-body.md  # gitlab
```
Wszystkie trzy trafienia są w bloku kopiowalnym dla człowieka (krok 5), żadne nie jest
czynnością skilla. `description` nie zawiera pushu/otwarcia PR jako czynności — mówi
wyłącznie, co skill przygotowuje i explicite neguje push/open/merge.

## zadanie 7.5 — grep po całym skills/

```
$ grep -rn 'git push\|pr create\|mr create\|release create' skills/
skills/ops-ship/SKILL.md:15:   git push -u origin <branch>
skills/ops-ship/SKILL.md:16:   gh pr create --body-file openspec/changes/<id>/pr-body.md        # github
skills/ops-ship/SKILL.md:17:   glab mr create --description-file openspec/changes/<id>/pr-body.md  # gitlab
```
Pozycja po pozycji:
- `skills/ops-ship/SKILL.md:15` `git push -u origin <branch>` — komenda wypisana człowiekowi w bloku kopiowalnym, nie wykonywana przez skill. Operacja przenosząca kod, ale nie jest czynnością agenta.
- `skills/ops-ship/SKILL.md:16` `gh pr create ...` — jak wyżej, dla hosta github.
- `skills/ops-ship/SKILL.md:17` `glab mr create ...` — jak wyżej, dla hosta gitlab.
- `skills/ops-review/SKILL.md:12` (`--comment`) — nie trafia w ten grep (nie zawiera `pr create`/`mr create`/`git push`/`release create`). Zgodnie z ustaleniem z brief: komentarz na istniejącym PR/MR zostaje, bo nie przenosi kodu — tylko dopisuje recenzję.
Brak innych trafień w `skills/`. Nie znaleziono żadnej pozycji, która kazałaby agentowi
zapisywać na zdalne poza tymi trzema wierszami przeznaczonymi dla człowieka — brak
concern do zgłoszenia z tego zadania.

## zadanie 8.1 — asercje w e2e_smoke.sh + test bramki

Dodane asercje w `tests/e2e_smoke.sh` (przed `echo "E2E_SMOKE_OK"`):
```
grep -q 'nie pushuje na żadne zdalne' AGENTS.md
grep -q 'Bash(git push\*)' .claude/settings.json
```
`jq` jest w `/usr/bin/jq` (czyli w zawężonym PATH e2e: `/usr/bin:/bin`), ale zostawiono
`grep -q` dla zgodności ze stylem skryptu i zerowych nowych zależności.

**Test bramki — usunięcie reguły z `templates/AGENTS.md` i potwierdzenie, że `make e2e` pada:**
```
$ sed -i '' '17d' templates/AGENTS.md
$ grep -n "nie pushuje" templates/AGENTS.md || echo "RULE_ABSENT (expected)"
RULE_ABSENT (expected)

$ make e2e
bash tests/e2e_smoke.sh
TODO: lint
TODO: typecheck
TODO: test
make: *** [e2e] Error 1
exit code: 2
```
**Przywrócenie reguły i potwierdzenie, że `make e2e` znów przechodzi:**
```
$ cp /tmp/templates-AGENTS.md.pre-gate-test.bak templates/AGENTS.md
$ grep -n "nie pushuje na żadne zdalne" templates/AGENTS.md
17:- Agent nie pushuje na żadne zdalne, nie otwiera ani nie merguje PR/MR, nie tworzy release'ów. Wynikiem pracy agenta jest commit w lokalnym repo; push, PR/MR i merge wykonuje człowiek. Komentarz z wynikiem review na istniejącym PR/MR jest dozwolony.

$ diff /tmp/templates-AGENTS.md.pre-gate-test.bak templates/AGENTS.md && echo IDENTICAL
IDENTICAL

$ make e2e
bash tests/e2e_smoke.sh
TODO: lint
TODO: typecheck
TODO: test
E2E_SMOKE_OK
exit code: 0
```
Dowód, że asercja faktycznie coś sprawdza (pada bez reguły, przechodzi z regułą), nie
jest dekoracją.

**Uwaga o stanie pliku:** `templates/AGENTS.md` miał już PRZED tym testem niezacommitowaną
zmianę w sekcji `## Konwencje` (dopisany zakaz trailerów AI), niezwiązaną z zadaniem 8.1
— widoczną też w `AGENTS.md` (korzeń). To nie jest zmiana wprowadzona w tym batchu (poza
zakresem: `skills/ops-ship/SKILL.md`, `tests/e2e_smoke.sh`, `evidence.md`), więc nie
została dotknięta ani wycofana. Backup `/tmp/templates-AGENTS.md.pre-gate-test.bak`
wzięty tuż przed testem bramki potwierdza, że plik wrócił dokładnie do stanu **sprzed
testu** (`diff` pusty, `IDENTICAL` powyżej) — a nie do stanu zacommitowanego w HEAD,
bo stan zacommitowany w HEAD różni się od stanu roboczego tą właśnie wcześniejszą,
niezależną zmianą:
```
$ git status --short templates/AGENTS.md
 M templates/AGENTS.md
$ git diff templates/AGENTS.md
@@ -24,5 +24,5 @@ Agent: 1. `make check` zielone. 2. Review bez BLOCKER. 3. evidence.md uzupełnio
 Człowiek: push gałęzi, otwarcie PR/MR z szablonu, merge.

 ## Konwencje
-- Gałęzie: feat/<id>, fix/<id>. Commity: Conventional Commits.
+- Gałęzie: feat/<id>, fix/<id>. Commity: Conventional Commits. Bez trailerów atrybucji AI (`Co-Authored-By: Claude ...`) w commitach ani w treści PR/MR — komunikat kończy się ostatnią linią treści.
 - TODO: styl kodu, pułapki, architektura (max 20 linii)
```
Zgłoszone jako concern w raporcie batcha C — plik nie jest w stanie zacommitowanym z
przyczyny niezależnej od tego zadania (prawdopodobnie ślad po `filter-branch`
wspomnianym w briefie, widoczny w `git reflog` jako `HEAD@{0}: filter-branch: rewrite`
na commicie `e8c2fb5`), a ten batch go nie naprawia, bo nie wolno edytować
`templates/AGENTS.md`/`AGENTS.md` poza samym testem bramki.

## zadanie 8.2 — bramki

```
$ make check
shellcheck scripts/deny-push.sh scripts/detect.sh scripts/format-file.sh scripts/init.sh scripts/install.sh scripts/protect-paths.sh scripts/stop-gate.sh tests/e2e_smoke.sh .githooks/pre-push templates/pre-push
typecheck OK
/Users/wojciechwylezol/PycharmProjects/ai-developer-ops/.venv/bin/python3 -m unittest discover -s tests -t .
...............................................................
----------------------------------------------------------------------
Ran 63 tests in 1.517s

OK
exit code: 0
```
```
$ make e2e
bash tests/e2e_smoke.sh
TODO: lint
TODO: typecheck
TODO: test
E2E_SMOKE_OK
exit code: 0
```
Oba 0.

## zadanie 8.3 — zakres

```
$ git diff --name-only bebc607d69bf143054e65b19aae1728812c72ed8
.claude/settings.json
AGENTS.md
scripts/deny-push.sh
scripts/protect-paths.sh
skills/ops-ship/SKILL.md
templates/AGENTS.md
templates/handoff.md
templates/settings.json
tests/e2e_smoke.sh
tests/test_hooks.py
```
```
$ git ls-files --others --exclude-standard
openspec/changes/local-commit-only/.openspec.yaml
openspec/changes/local-commit-only/critique.md
openspec/changes/local-commit-only/design.md
openspec/changes/local-commit-only/evidence.md
openspec/changes/local-commit-only/handoff.md
openspec/changes/local-commit-only/proposal.md
openspec/changes/local-commit-only/specs/agent-guardrails/spec.md
openspec/changes/local-commit-only/tasks.md
```
Obie listy razem wymieniają wyłącznie: pliki z sekcji Impact `proposal.md` (10 plików z
diffa: `.claude/settings.json`, `AGENTS.md`, `scripts/deny-push.sh`,
`scripts/protect-paths.sh`, `skills/ops-ship/SKILL.md`, `templates/AGENTS.md`,
`templates/handoff.md`, `templates/settings.json`, `tests/e2e_smoke.sh`,
`tests/test_hooks.py` — wszystkie są w sekcji Impact) oraz pliki w
`openspec/changes/local-commit-only/` (8 plików z `ls-files --others`). Żadnej pozycji
poza tymi dwoma zbiorami. `scripts/deny-push.sh` jest widoczny w pierwszej liście
(diff), bo jest już zacommitowany od batcha A/B — nie zgubiony przez kontrolę
zakresu.
