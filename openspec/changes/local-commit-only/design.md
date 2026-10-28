# Design

## Context

Zobacz `proposal.md` — Why. Stan faktyczny, sprawdzony w repo:

- `.claude/settings.json` i `templates/settings.json` są identyczne: `allow` zawiera `"Bash(git *)"`, `deny` tylko `"Bash(git push --force*)"` i `"Bash(git push -f*)"`. Stąd `git push origin HEAD:main` nie wywołał nawet promptu.
- `hooks/hooks.json` rejestruje trzy hooki: `PreToolUse` na `Edit|Write|MultiEdit` → `protect-paths.sh`, `PostToolUse` na to samo → `format-file.sh`, `Stop` → `stop-gate.sh` (timeout 900).
- Kontrakt hooka blokującego z `scripts/protect-paths.sh`: JSON na stdin, pole przez `jq`, `exit 2` blokuje z komunikatem na stderr, `exit 0` przepuszcza. Furtka `AIDEVOPS_ALLOW_PROTECTED=1`. Wzorzec chronionych ścieżek nie obejmuje dziś `hooks/`, `scripts/` ani `settings.json`.
- Udokumentowana pułapka w `AGENTS.md`: `protect-paths` **przepuszcza**, gdy brak `jq`.
- `skills/ops-ship/SKILL.md:8` instruuje agenta: `git push -u origin <branch>`; `:9` wywołuje `gh pr create`/`glab mr create`; `:10` prosi o review komentarzem. Frontmatter: "Commit, push, open a PR ... Never merges", `disable-model-invocation: true`.
- `skills/ops-review/SKILL.md:12` instruuje dodanie `--comment` dla celu PR/MR.
- `AGENTS.md:22` — Definition of Done punkt 5: "PR/MR z szablonu".
- `tests/e2e_smoke.sh:7` ma `trap 'rm -rf "$TMP"' EXIT`, więc katalog tymczasowy nie istnieje po zakończeniu. Skrypt podstawia atrapy `claude`/`codex` zwracające `exit 0`.
- `tests/test_hooks.py` testuje hooki przez `run_script` + `stub_env` z `tests/util.py`: JSON na stdin, asercje na kodzie wyjścia i stderr.
- Bash musi być zgodny z bash 3.2 (macOS): bez `mapfile`, bez tablic asocjacyjnych.

## Goals / Non-Goals

**Goals:**
- Bezpośrednie wywołanie operacji przenoszącej kod na zdalne jest zablokowane, niezależnie od nazwy zdalnego, podania URL, separatora powłoki i przekierowania katalogu przez `-C`.
- Tekst opisujący zabronioną komendę przechodzi — bramka nie może blokować przygotowania materiałów dla człowieka.
- Bramka chroni własną konfigurację: jedna edycja nie może jej wyłączyć.
- Niemożność oceny komendy skutkuje odmową, ale tylko dla komend wyglądających na zapis na zdalne.
- Zakaz jest obecny także w instrukcjach dla wariantu bez hooków i w świeżo zainicjalizowanym projekcie.

**Non-Goals:**
- **To nie jest sandbox.** Agent, który celowo chce obejść bramkę, obejdzie ją: napisze skrypt i go uruchomi, użyje `curl` do API hostingu albo narzędzia MCP z dostępem do sieci. Bramka zatrzymuje domyślną ścieżkę i przypadkowe wykonanie, nie przeciwnika. Tak postanowił użytkownik po przedstawieniu alternatywy twardszej bariery. Spec nie obiecuje więcej, niż bramka daje — pierwotna wersja obiecywała blokadę "niezależnie od narzędzia", co było nieprawdą i zostało wycofane po `critique.md` BLOCKER 1 i 2.
- Nie blokujemy komentowania PR/MR. Decyzja użytkownika: zakaz dotyczy operacji przenoszących kod, nie publikacji wyniku review. Dlatego `skills/ops-review/SKILL.md:12` i prośba o review w `ops-ship` zostają bez zmian.
- Nie opisujemy specem istniejących bramek `protect-paths` i `stop-gate` poza tym, co ta zmiana dodaje (ochrona plików bramki).
- Nie usuwamy `.githooks/pre-push`. Push człowieka nadal przechodzi przez `make check`.
- Nie przechwytujemy `curl`, bibliotek ani narzędzi MCP. Wynika z non-goalu "to nie jest sandbox".

## Decisions

**1. Model zagrożeń: bariera przed domyślną ścieżką, nie sandbox.** Hook nie może być granicą bezpieczeństwa wobec agenta, który potrafi zapisać plik i go uruchomić — a agent to potrafi, bo zapisywanie skryptów jest jego normalną pracą. Wybór użytkownika: bariera. Konsekwencja dla speca: wymagania mówią o "bezpośrednim wywołaniu", a non-goal mówi wprost, czego bramka nie daje. Alternatywa (twarda bariera: `init.sh` ustawia martwy push-URL, który odblokowuje tylko człowiek) odpadła jako wybór użytkownika — była droższa i nadal nie szczelna.

**2. Hook jako główna warstwa, wzorce `deny` jako druga.** Wzorce dopasowują prefiks komendy, więc `Bash(git push*)` nie złapie `git -C /x push` ani `make check && git push`. Hook dostaje całą komendę w `.tool_input.command`. Odwrotnie, `deny` działa tam, gdzie hook może nie działać: w podagentach i w projekcie, który dostał `settings.json` bez `hooks.json`. Żadna warstwa osobno nie wystarcza.

**3. Dopasowanie operacji w pozycji komendy, po usunięciu cytowanych fragmentów.** Kolejność: (a) usuń z komendy zawartość apostrofów i cudzysłowów — to sprawia, że `git commit -m 'Dokumentuje git push'` i `printf '%s' 'git push origin x'` przechodzą; (b) na tym, co zostało, dopasuj operację w pozycji komendy, czyli na początku łańcucha albo po `;`, `&&`, `||`, `|`, nowej linii lub `(`. To spełnia wymaganie "tekst jako dane" ze speca. Granice tej metody (heredoc, nazwa podkomendy w zmiennej, `git pu""sh`) należą do non-goalu z decyzji 1 i są tam wymienione, a nie przemilczane. Alternatywa (regex na całym ciągu bez usuwania cudzysłowów) odpadła: blokowałaby zapis `pr-body.md`, czyli to, co bramka ma umożliwiać.

**4. Dopasowujemy operacje, nie binarki, a `gh api` po metodzie HTTP.** `deny` na `Bash(gh *)` zabiłoby `gh api --method POST /markdown`, jedyny prawdziwy dowód renderu GFM w tym repo. Dlatego: blokujemy `git push`, `gh pr create|merge`, `gh release create`, `glab mr create|merge`, oraz `gh api` z metodą zapisującą (`POST`, `PATCH`, `PUT`, `DELETE`, przez `--method` albo `-X`) **poza** jawną listą dozwolonych ścieżek, na której jest `/markdown`. Czasownik i metoda, nie nazwa narzędzia.

**5. Odmowa przy niemożności oceny, ale tylko dla komend ryzykownych.** Pierwotna decyzja ("brak `jq` blokuje") przeczyła wymaganiu, że praca lokalna przechodzi bezwarunkowo — `critique.md` WARN 6. Rozwiązanie dwustopniowe: najpierw tani pre-filtr na surowym wejściu, bez `jq` — jeśli w całym wejściu nie ma żadnego ciągu wskazującego na operację zapisu, przepuść; jeśli jest, a `jq` jest dostępne, oceń dokładnie; jeśli jest, a `jq` nie ma, zablokuj z komunikatem o niemożności oceny. To daje: brak `jq` nie blokuje pracy lokalnej, a jednocześnie nie przepuszcza pushu. Ten sam kontrakt obejmuje nieparsowalny JSON, pole puste, `null` i zły typ. `exit 2` i komunikat są jawne, nie pozostawione `set -e`.

**6. Bramka chroni własne pliki przez rozszerzenie `protect-paths.sh`.** Dodajemy do wzorca chronionych ścieżek: `scripts/deny-push.sh`, `hooks/hooks.json`, `.claude/settings.json`, `templates/settings.json`. Używamy istniejącego mechanizmu zamiast nowego, bo kontrakt (`exit 2`, furtka `AIDEVOPS_ALLOW_PROTECTED=1` dla człowieka) już jest i jest przetestowany. Furtka jest tu właściwa: człowiek musi móc zmienić bramkę.

**7. Brak furtki środowiskowej dla samego zakazu pushu.** W odróżnieniu od `protect-paths`, `deny-push.sh` nie ma `AIDEVOPS_ALLOW_*`. Furtka, którą agent może sam ustawić, nie jest zakazem. Push wykonuje człowiek ze swojej powłoki.

**8. `ops-ship` przygotowuje, człowiek wykonuje; treść PR/MR do pliku.** Skill zachowuje weryfikację warunków wstępnych, szablon i zbieranie dowodów, a kończy: treść PR/MR zapisana do `openspec/changes/<id>/pr-body.md`, wypisane komendy dla człowieka (`git push -u origin <branch>`, `gh pr create --body-file ...` albo `glab mr create --description ...`). Plik, nie komunikat, bo przeklejanie wielolinijkowego Markdowna z terminala gubi formatowanie. Prośba o review botów (`:10`) zostaje — komentarze są dozwolone.

**9. Definition of Done dzieli się na część agenta i część człowieka.** `AGENTS.md:22` wymaga dziś "PR/MR z szablonu", czego agent już nie może zrobić. Rozdzielamy: DoD agenta kończy się na zielonej bramce, review bez BLOCKER-a, uzupełnionym `evidence.md`, zgodnym specu i **przygotowanej** treści PR/MR plus lokalnym commicie. Otwarcie PR/MR jest krokiem człowieka. Bez tego repo wymagałoby od agenta rzeczy zabronionej — `critique.md` BLOCKER 4.

**10. Kolejność: artefakty przed commitem.** `pr-body.md` i `handoff.md` powstają **przed** końcowym commitem, żeby wynik pracy był w commicie, a nie poza nim (`critique.md` WARN 11). Oba pliki są wersjonowane — leżą w katalogu zmiany, który i tak wchodzi do commita.

**11. Zmianę wprowadzamy najpierw w `templates/`, potem odświeżamy kopie.** Konwencja z `AGENTS.md`: `templates/` jest źródłem prawdy, pliki w korzeniu to kopie z `init.sh`. Odwrotna kolejność sprawiłaby, że nowe projekty nie dostają zakazu.

## Risks / Trade-offs

- **Hook może zablokować człowieka** → jeśli `PreToolUse` odpala się także dla komend z prefiksem `!`, bramka zablokuje push człowieka. Nie wiem tego. Zadanie 1.1 rozstrzyga empirycznie, z **kontrolą dodatnią** (komenda agenta widoczna w tym samym logu i tej samej sesji), bo pusty log sam w sobie znaczy tylko tyle, że hook się nie załadował — `critique.md` WARN 7. Jeśli bramka widzi człowieka, zadanie 1.2 zatrzymuje się i pyta użytkownika; wybór słabszego mechanizmu wymaga wtedy aktualizacji speca, nie tylko planu (WARN 8).
- **Obejście przez skrypt, `curl`, MCP** → świadomie poza zakresem, patrz non-goal i decyzja 1. Zapisane jako ograniczenie, nie przemilczane.
- **Dwie warstwy mogą się rozjechać** → lista operacji żyje w hooku i we wzorcach `deny`. Źródłem prawdy jest hook; `deny` to zgrubna siatka. Test pokrywa hook; `jq empty` sprawdza tylko składnię `settings.json`. Rozjazd listy zostaje ryzykiem rezydualnym.
- **Fałszywe blokady** → mimo usuwania cytowanych fragmentów regex może trafić w coś niewinnego. Testy zawierają przypadki niewinne (commit z opisem, `git log --grep=push`, zapis instrukcji do pliku), nie tylko złośliwe.
- **Istniejące projekty nie dostaną zakazu automatycznie** → `init.sh` używa `cp_if_absent`, więc projekt z własnym `settings.json`/`AGENTS.md` zachowa stare pliki. Trzeba to powiedzieć użytkownikowi w raporcie; nie nadpisujemy plików użytkownika.
- **`make e2e` nie udowodni ochrony w świeżym projekcie bez zmiany smoke testu** → `trap rm -rf` usuwa katalog, a atrapy `claude`/`codex` zwracają `exit 0`. Asercje muszą trafić do `tests/e2e_smoke.sh` przed teardownem, co rozszerza listę Impact o ten plik (`critique.md` WARN 10).
- **Warstwa `deny` nie pokrywa `gh api`** → `deny` dopasowuje tylko prefiksy wzorców, więc nie umie wyrazić wyjątku „POST jest zablokowane, poza `/markdown`" — a `gh api --method POST /markdown` jest jawnie dozwolone w specu (dowód renderu GFM). Dodanie `Bash(gh api*)` do `deny` zablokowałoby też ten dozwolony przypadek; dodanie węższego wzorca (np. po metodzie) nie jest wyrażalne we wzorcach prefiksowych `deny`. Egzekwowanie zakazu zapisu przez `gh api` spoczywa więc wyłącznie na hooku (`scripts/deny-push.sh`, etap 7), nie na drugiej warstwie. W projekcie, który dostał `settings.json` bez `hooks/hooks.json` (patrz decyzja 2), `gh api` z metodą zapisującą nie jest tam zablokowane przez żadną warstwę. To ryzyko rezydualne, nie do zamknięcia w tej zmianie.

## Open Questions

- Czy `hooks/hooks.json` z matcherem `Bash` wymaga dokładnie tej nazwy narzędzia, czy wzorca. Rozstrzygalne przy implementacji testem bramki; nie zmienia speca ani podziału zadań.
