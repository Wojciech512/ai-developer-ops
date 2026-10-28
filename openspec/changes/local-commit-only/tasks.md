# Tasks

TDD: w obrębie zadania test jest najpierw czerwony, potem zielony. `make check` musi być zielone **na końcu każdego zadania**, nie w jego środku — zadanie 2.1 celowo zostawia czerwony test i dlatego jest połączone z 2.2 w jedno zadanie (`critique.md` NOTE 13).

Baza do pomiaru zakresu: zadanie 0.1 zapisuje SHA przed pierwszą edycją kodu.

## 0. Baza

- [x] 0.1 Zapisać bazę: `git rev-parse HEAD` oraz `git ls-files --others --exclude-standard` do sekcji `## baseline` w `openspec/changes/local-commit-only/evidence.md`, przed jakąkolwiek edycją kodu. Weryfikacja: oba wyniki są w `evidence.md`, a commit bazowy zgadza się z `git log -1 --format=%H`.

## 1. Rozstrzygnąć ryzyko blokowania człowieka

- [ ] 1.1 Ustalić empirycznie, czy hook `PreToolUse` na `Bash` widzi komendy wpisywane przez człowieka z prefiksem `!`. Metoda: tymczasowy hook logujący `.tool_input.command` do pliku i zawsze zwracający 0. **Kontrola dodatnia jest obowiązkowa**: najpierw agent wykonuje rozpoznawalną komendę (np. `echo HOOK_PROBE_AGENT`) i potwierdza, że wpis jest w logu — bez tego pusty log po komendzie człowieka nie dowodzi niczego poza tym, że hook się nie załadował. Potem poprosić użytkownika o wpisanie `! echo HOOK_PROBE_HUMAN` i sprawdzić log. Weryfikacja: `evidence.md` zawiera treść logu z widocznym wpisem agenta (kontrola dodatnia przeszła) oraz informację, czy wpis człowieka też tam jest. To zadanie NIE rejestruje hooka blokującego i usuwa hook logujący po pomiarze.
- [ ] 1.2 Jeśli 1.1 pokaże, że hook widzi komendy człowieka: zatrzymać się i zaraportować użytkownikowi, że bramka zablokuje też jego pushe, i poprosić o decyzję. Jeśli użytkownik wybierze słabszy mechanizm, zaktualizować **spec** (`specs/agent-guardrails/spec.md`), nie tylko plan — rezygnacja z hooka zmienia to, co system obiecuje (`critique.md` WARN 8). Weryfikacja: albo kontrola dodatnia przeszła i wpisu człowieka nie ma, więc zadanie jest nieaktywne, albo istnieje raport dla użytkownika i zadanie 3 nie zostało rozpoczęte.

## 2. Hook deny-push (TDD, jedno zadanie od czerwonego do zielonego)

- [x] 2.1 Napisać testy w `tests/test_hooks.py` (klasa `DenyPush`, wzorem `ProtectPaths`; stdin to `{"tool_input": {"command": "..."}}`), zobaczyć je czerwone, potem napisać `scripts/deny-push.sh` aż będą zielone.
      Blokujące (exit 2 + komunikat na stderr): `git push`, `git push origin HEAD:main`, `git push https://github.com/x/y.git HEAD:main`, `git push upstream main`, `git -C /tmp/x push`, `make check && git push`, `git status; git push`, `gh pr create`, `gh pr merge`, `gh release create`, `glab mr create`, `glab mr merge`, `gh api --method POST /repos/o/r/git/refs`, `gh api -X DELETE /repos/o/r`.
      Przepuszczające (exit 0): `git commit -m x`, `git commit -m "Dokumentuje git push"`, `printf '%s' 'git push origin x'`, `git status`, `git fetch`, `git log --grep=push`, `make check`, `gh pr view 1`, `gh pr list`, `gh api --method POST /markdown`, `gh api /repos/o/r`, pusty JSON `{}`.
      Skrypt: `set -euo pipefail`, jawny `exit 2` z komunikatem (nie poleganie na `set -e`), usunięcie cytowanych fragmentów przed dopasowaniem, dopasowanie operacji w pozycji komendy (początek albo po `;`, `&&`, `||`, `|`, nowej linii, `(`) — decyzja 3 w `design.md`. Zgodność z bash 3.2.
      Weryfikacja: `python3 -m unittest tests.test_hooks -k DenyPush` zielone, `shellcheck scripts/deny-push.sh` czysty, `make check` zielone.
- [x] 2.2 Dodać testy kontraktu niemożności oceny (decyzja 5 w `design.md`): brak `jq` + komenda ryzykowna → exit 2 z komunikatem o niemożności oceny; brak `jq` + komenda zwykła → exit 0; nieparsowalny JSON, pole `null`, pole liczbowe → ta sama zasada. Weryfikacja: testy zielone; w szczególności test "brak `jq` + `make check`" przechodzi, co dowodzi, że bramka nie blokuje pracy lokalnej bez `jq` — celowa różnica wobec `protect-paths.sh`, udokumentowana w `design.md`.

## 3. Rejestracja hooka i dowód działania

- [ ] 3.1 Dodać wpis do `hooks/hooks.json`: `PreToolUse` z matcherem `Bash` wołający `bash "${CLAUDE_PLUGIN_ROOT}/scripts/deny-push.sh"`. Weryfikacja: `jq empty hooks/hooks.json` przechodzi, `jq '[.hooks.PreToolUse[]] | length' hooks/hooks.json` daje 2, `make check` zielone.
- [ ] 3.2 Dowód **zatrzymania wywołania**, nie tylko odpowiedzi skryptu (`critique.md` WARN 9). Użyć celu, który nie może nawiązać połączenia — zdalnego o nazwie nieistniejącej w konfiguracji, np. `git push aidevops-nonexistent-remote HEAD:main`. **Nie używać `--dry-run`**: `git push --dry-run` nawiązuje połączenie ze zdalnym, więc nie dowodziłby braku kontaktu. Weryfikacja: w `evidence.md` jest (a) wyjście zablokowanej próby z komunikatem bramki, (b) dowód, że komenda nie została wykonana — brak w logu `git` jakiegokolwiek odwołania do zdalnego, (c) wyjście `git status` i `make check` jako przypadki przepuszczone, (d) wskazanie, która warstwa zablokowała (hook czy `deny`).

## 4. Warstwa deny w settings

- [x] 4.1 Dodać do `templates/settings.json` (źródło prawdy) wpisy `deny`: `Bash(git push*)`, `Bash(gh pr create*)`, `Bash(gh pr merge*)`, `Bash(gh release create*)`, `Bash(glab mr create*)`, `Bash(glab mr merge*)`, zachowując istniejące wpisy. NIE dodawać `Bash(gh *)` — zabiłoby `gh api --method POST /markdown` (decyzja 4). Weryfikacja: `jq empty templates/settings.json`; `jq -r '.permissions.deny[]' templates/settings.json` wymienia nowe wpisy; `jq -r '.permissions.deny[]' templates/settings.json | grep -cx 'Bash(gh \*)'` daje 0.
- [x] 4.2 Odświeżyć kopię `.claude/settings.json`. Weryfikacja: `diff templates/settings.json .claude/settings.json` pusty, `make check` zielone.

## 5. Ochrona plików bramki

- [x] 5.1 Rozszerzyć wzorzec w `scripts/protect-paths.sh` o `scripts/deny-push.sh`, `hooks/hooks.json`, `.claude/settings.json`, `templates/settings.json` (decyzja 6). Najpierw test w klasie `ProtectPaths`: każda z tych ścieżek daje exit 2, a `AIDEVOPS_ALLOW_PROTECTED=1` je przepuszcza. Weryfikacja: nowe testy zielone, istniejące testy `ProtectPaths` nadal zielone, `shellcheck` czysty, `make check` zielone.

## 6. Reguła dla wariantu bez hooków i nowych projektów

- [x] 6.1 Dopisać regułę do `## Proces` w `templates/AGENTS.md`: agent nie pushuje na **żadne** zdalne (nie tylko `origin`), nie otwiera ani nie merguje PR/MR, nie tworzy release'ów; wynikiem pracy jest commit w lokalnym repo; push, PR/MR i merge wykonuje człowiek; komentarze z wynikiem review są dozwolone. Weryfikacja: reguła jest w pliku, wymienia "dowolne zdalne" i release'y (`critique.md` BLOCKER 3), a `grep -c '' templates/AGENTS.md` daje nie więcej niż 60.
- [x] 6.2 Rozdzielić Definition of Done w `templates/AGENTS.md` na część agenta i część człowieka (decyzja 9): agent kończy na zielonej bramce, review bez BLOCKER-a, uzupełnionym `evidence.md`, zgodnym specu, przygotowanej treści PR/MR i lokalnym commicie; otwarcie PR/MR to krok człowieka. Weryfikacja: punkt 5 nie wymaga już od agenta utworzenia PR/MR; `grep -n 'Definition of Done' -A3 templates/AGENTS.md` pokazuje rozdzielenie.
- [x] 6.3 Odświeżyć kopię `AGENTS.md` w korzeniu. Weryfikacja: fragmenty `## Proces` i `## Definition of Done` obu plików identyczne (porównanie przez pliki tymczasowe, nie podstawienie procesu — bash 3.2), `grep -c '' AGENTS.md` nie więcej niż 60.
- [x] 6.4 Dodać status `ready-to-push` do listy statusów w `templates/handoff.md` i `.aidevops/templates/handoff.md` (`critique.md` NOTE 14). Weryfikacja: `grep -n 'ready-to-push' templates/handoff.md` trafia; lista statusów zawiera go obok istniejących.

## 7. Przeprojektowanie ops-ship

- [x] 7.1 Usunąć z `skills/ops-ship/SKILL.md` instrukcje wykonania: `git push -u origin <branch>` (krok 1) i `gh pr create`/`glab mr create` (krok 2). Zostawić krok 3 (prośba o review botów) — komentarze są dozwolone decyzją użytkownika. Weryfikacja: `grep -n 'git push\|pr create\|mr create' skills/ops-ship/SKILL.md` pokazuje te ciągi wyłącznie w kontekście "wypisz człowiekowi", nigdy jako czynność skilla.
- [x] 7.2 Dodać do `skills/ops-ship/SKILL.md` krok zapisu wypełnionej treści PR/MR do `openspec/changes/<id>/pr-body.md` oraz krok wypisania komend dla człowieka (`git push -u origin <branch>`, `gh pr create --body-file openspec/changes/<id>/pr-body.md` albo `glab mr create --description-file ...`). Kolejność: `pr-body.md` i `handoff.md` **przed** końcowym commitem (decyzja 10). Weryfikacja: skill opisuje tę kolejność jawnie; `pr-body.md` jest w katalogu zmiany, więc wchodzi do commita.
- [x] 7.3 Opisać w `skills/ops-ship/SKILL.md` zachowanie w przypadkach brzegowych (`critique.md` WARN 12): warunki wstępne niespełnione → stop z raportem, bez przygotowywania; `pr-body.md` już istnieje → nadpisz i powiedz o tym; brak zmian do commita → powiedz i nie twórz pustego commita; `handoff.md` ustawiany na `status=ready-to-push`, `owner=human`. Weryfikacja: każdy z czterech przypadków ma w skillu jedno zdanie mówiące, co się dzieje.
- [x] 7.4 Zaktualizować `description` we frontmatterze `skills/ops-ship/SKILL.md` — obiecuje dziś "Commit, push, open a PR". Weryfikacja: `description` nie przedstawia pushu ani otwarcia PR jako czynności skilla; `make check` zielone (walidacja TOML/JSON nie dotyczy, ale bramka musi przejść).
- [x] 7.5 Przejrzeć pozostałe skille pod kątem instrukcji zapisu na zdalne. Weryfikacja: `grep -rn 'git push\|pr create\|mr create\|release create' skills/` przejrzane pozycja po pozycji; wynik (co jest operacją przenoszącą kod, co nie) zapisany w `evidence.md`. Wiadomo z góry, że `skills/ops-review/SKILL.md:12` (`--comment`) zostaje — komentarze są dozwolone.

## 8. Dowody i bramki

- [x] 8.1 Rozszerzyć `tests/e2e_smoke.sh` o asercje **przed** teardownem (`trap rm -rf` usuwa katalog, `critique.md` WARN 10): wygenerowany projekt ma nową regułę w `AGENTS.md` i nowe wpisy `deny` w `.claude/settings.json`. Weryfikacja: `make e2e` kończy się kodem 0 i wypisuje `E2E_SMOKE_OK`; celowe usunięcie reguły z `templates/AGENTS.md` sprawia, że `make e2e` pada (test bramki), po czym reguła wraca.
- [x] 8.2 Uruchomić `make check` i `make e2e`, wkleić wyniki z kodami wyjścia do `evidence.md`. Weryfikacja: oba kończą się kodem 0.
- [x] 8.3 Potwierdzić zakres wobec bazy z 0.1, uwzględniając pliki nieśledzone (`critique.md` NOTE 15). Weryfikacja: `git diff --name-only <baza>` oraz `git ls-files --others --exclude-standard` razem wymieniają wyłącznie pliki z sekcji Impact w `proposal.md` i pliki w `openspec/changes/local-commit-only/`; nowy `scripts/deny-push.sh` jest widoczny w jednej z tych list, a nie pominięty.

## Workflow follow-up

- Review: `ops-review local-commit-only`; właściciel naprawia każdy BLOCKER i WARN, potem powtarza do PASS.
- Wynikiem jest commit na `feat/local-commit-only` w lokalnym repo. Agent nie pushuje — to reguła, którą ta zmiana wprowadza. Push, PR i merge wykonuje człowiek.
- Po merge: `/opsx:archive local-commit-only`.
