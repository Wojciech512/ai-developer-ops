# Critique: local-commit-only

Krytyk: `codex exec -m gpt-6-astra -c model_reasoning_effort=high` (wariant claude-codex).
Wejście: proposal.md, specs/agent-guardrails/spec.md, design.md, tasks.md.
Data: 2026-10-28. **Werdykt krytyka: FAIL** — 4 BLOCKER, 8 WARN, 3 NOTE.

## critical

1. **BLOCKER — `design.md:50`, `specs/agent-guardrails/spec.md:10`: projekt świadomie dopuszcza złamanie głównego wymagania.** Spec obiecuje blokadę niezależną od narzędzia i składni, a design dopuszcza skrypt wykonujący push. Test 2.1 wręcz wymaga przepuszczenia `bash scripts/push.sh`, chociaż hook nie zna zawartości tego pliku. Agent może zapisać skrypt i go uruchomić. „Agent nie ma powodu tego robić" nie jest mechanizmem bezpieczeństwa. Trzeba albo ograniczyć deklarację do wykrywania wybranych bezpośrednich wywołań, albo przenieść egzekwowanie poza kontrolę agenta.

2. **BLOCKER — `design.md:38`, `specs/agent-guardrails/spec.md:10`: sześć komend nie pokrywa zakazu zapisu.** Ta sama operacja może być wykonana przez API, klienta HTTP, bibliotekę albo narzędzie MCP. Dopuszczenie konkretnego endpointu renderowania Markdown nie uzasadnia przepuszczania pozostałych operacji API. Lista czasowników nie stanowi granicy uprawnień. Brakuje również określenia, czy chronione są konfiguracja bramki, jej skrypt i dostępne agentowi poświadczenia.

3. **BLOCKER — `tasks.md:29`, `specs/agent-guardrails/spec.md:46`: wariant Codex nie otrzymuje deklarowanej ochrony.** Obecność zdania w AGENTS.md dowodzi wyłącznie obecności instrukcji. Nie dowodzi mechanicznego zablokowania operacji. Ponadto planowane zdanie zabrania pushowania **na `origin`**, zamiast na dowolny remote lub URL, i pomija release'y. Scenariusz specyfikacji sprawdza tekst, mimo że wymaganie nadrzędne obiecuje działający zakaz.

4. **BLOCKER — `tasks.md:35`, `templates/AGENTS.md:22`: plan pozostawia sprzeczny workflow.** Istniejący `skills/ops-review/SKILL.md:12` nakazuje publikację komentarza, a `skills/ops-ship/SKILL.md:10` żądanie review przez komentarze/notatki. Zadanie 6.2 pozwala zakończyć się samym raportem o tym konflikcie. Równocześnie Definition of Done nadal wymaga PR/MR, choć agent ma kończyć na lokalnym commicie. Usunięcie sprzecznych instrukcji i rozdzielenie zakończenia pracy agenta od działań człowieka musi należeć do tej zmiany.

## major

5. **WARN — `tasks.md:13`, `design.md:49`: testy nie odróżniają polecenia od tekstu opisującego polecenie.** Brakuje dozwolonych przypadków takich jak `git commit -m 'Document git push'`, `printf '%s\n' 'git push origin feature'` czy heredoc zapisujący instrukcje do `pr-body.md`. Regex może blokować przygotowanie wymaganego handoffu. Po stronie obejść brakuje choćby `git pu""sh`, zmiennej zawierającej nazwę podkomendy, nowych linii i deklarowanego separatora `;`. Testowanie dziewięciu napisów nie dowodzi rozpoznawania operacji powłoki.

6. **WARN — `tasks.md:13–15`, `design.md:36`: zasada odmowy przy braku możliwości oceny jest niespójna.** Brak `jq` ma blokować, ale brak pola komendy w `{}` ma przepuszczać. Nie określono zachowania dla uszkodzonego JSON, `null`, niewłaściwego typu ani błędu `jq`. `set -e` nie gwarantuje wymaganego `exit 2` i komunikatu. Jednocześnie blokowanie każdego Bash przy braku `jq` przeczy bezwarunkowemu wymaganiu przepuszczania pracy lokalnej w `spec.md:30`. Potrzebny jest jawny warunek dostępności zależności oraz kontrakt obsługi błędów.

7. **WARN — `tasks.md:8`: eksperyment z `! git status` może dać fałszywy wynik.** Pusty log może oznaczać, że hook w ogóle się nie załadował. Brakuje kontroli dodatniej: polecenia wykonanego przez agenta, widocznego w tym samym logu i tej samej sesji. Bez niej zadanie 1.2 może zostać pominięte na podstawie niedziałającego eksperymentu.

8. **WARN — `tasks.md:9`, `design.md:48`: fallback nie spełnia specyfikacji.** Rezygnacja z hooka zostawia warstwę, którą sam design w linii 32 uznaje za niewystarczającą. Plan nie wymaga wtedy aktualizacji specyfikacji, kryteriów odbioru i dalszych zadań. Zgoda na słabszy mechanizm nie sprawia, że dotychczasowe wymaganie jest spełnione. Nie zbadano też, czy proponowany fallback rozwiązuje problem komend człowieka.

9. **WARN — `tasks.md:19–24`: dowody konfiguracji zastępują dowody działania.** Liczba wpisów w `PreToolUse`, poprawny JSON i obecność wzorców nie dowodzą uruchomienia właściwego hooka ani działania `deny`. Testy jednostkowe sprawdzają odpowiedź skryptu, nie zatrzymanie wykonania narzędzia. Test integracyjny powinien wykazać, że kontrolowane polecenie nie zostało uruchomione, wskazać blokującą warstwę i pokrywać osobno hook, permissions oraz deklarowany przypadek podagenta. Próba `git push --dry-run` bez kontrolowanego celu nie dowodzi braku kontaktu ze zdalnym repozytorium.

10. **WARN — `tasks.md:40`, `tests/e2e_smoke.sh:7`: zadanie 7.2 jest niewykonalne w opisanej kolejności.** Smoke test usuwa katalog tymczasowy przy zakończeniu, więc po `make e2e` nie ma projektu do sprawdzenia. Ponadto podstawia atrapy Claude i Codexa oraz sprawdza wariant mieszany; nie testuje rzeczywistej ochrony w obu narzędziach. Asercje trzeba wykonać przed usunięciem katalogu albo w osobnym fixture. Zmiana smoke testu wymaga rozszerzenia listy Impact.

11. **WARN — `tasks.md:34`: commit powstaje przed końcowymi artefaktami.** Kolejność „commit → `pr-body.md` → aktualizacja `handoff.md`" zostawia wynik pracy poza deklarowanym commitem. Brakuje decyzji, czy te pliki mają być wersjonowane, oraz kontroli końcowego stanu drzewa.

12. **WARN — `tasks.md:34`: odbiór przebudowy `ops-ship` nie sprawdza jej zachowania.** `grep` nie dowodzi zatrzymania przy czerwonej bramce, nierozwiązanym BLOCKER-ze ani przygotowania poprawnej treści z szablonu. Zadanie 6.1 łączy warunki wstępne, commit, dwa hosty, plik treści i przekazanie odpowiedzialności. Potrzebuje oddzielnych kryteriów oraz przypadków: ponowne uruchomienie, istniejący `pr-body.md`, brak zmian do commita i niepowodzenie zapisu pliku.

## minor

13. **NOTE — `tasks.md:4`, `tasks.md:13`: wymagania procesu wzajemnie się wykluczają.** Po każdym zadaniu `make check` ma być zielone, ale zadanie 2.1 kończy się celowo czerwonym testem. Z kolei test braku `jq` powstaje po implementacji tego zachowania. Trzeba poprawić granice zadań lub jawnie określić wyjątki od deklarowanego TDD.

14. **NOTE — `tasks.md:34`, `templates/handoff.md:2`: nowy status nie istnieje w szablonie.** `ready-to-push` nie należy do wymienionych statusów. Szablon handoffu nie jest objęty Impact.

15. **NOTE — `tasks.md:41`: kontrola zakresu pomija pliki nieśledzone.** `git diff --name-only <baza>` nie ujawni nowych, niedodanych plików — może więc „potwierdzić zakres", pomijając właśnie nowy hook. Plan nie zawiera też kroku zapisania bazy.

## open questions

- `specs/agent-guardrails/spec.md:10`: czy celem jest odporność na celowe obejście, czy ograniczenie przypadkowego wykonania kilku komend? Obecne artefakty obiecują pierwsze, projektują drugie.
- `design.md:38`: co dokładnie oznacza „zapis na zdalne": również komentarze, edycja PR, tagi, ustawienia repozytorium i uruchamianie workflow?
- `design.md:34`: czy człowiek ma wykonywać komendy w osobnym terminalu, czy również przez `!`?
- `specs/agent-guardrails/spec.md:30`: co ma się stać, gdy dozwolone `git commit` uruchamia lokalny hook wykonujący zapis zdalny albo dozwolone `make` wywołuje skrypt z pushem?
- `tasks.md:34`: skąd pochodzą konkretne remote, gałąź docelowa i tytuł PR/MR, oraz jak sprawdzane będzie cytowanie wielolinijkowej treści dla obu hostów?

## Weryfikacja twierdzeń krytyka (nie przyjęte na słowo)

Sprawdzone bezpośrednio w repo, wszystkie cztery potwierdzone:

- WARN 10: `tests/e2e_smoke.sh:7` ma `trap 'rm -rf "$TMP"' EXIT` — katalog tymczasowy nie istnieje po `make e2e`. Dodatkowo skrypt podstawia atrapy `claude`/`codex` zwracające `exit 0`, więc nie testuje realnej ochrony.
- BLOCKER 4: `skills/ops-review/SKILL.md:12` każe dodać `--comment` dla celu PR/MR; `skills/ops-ship/SKILL.md:10` każe komentować `@codex review` i publikować notatkę w MR; `AGENTS.md:22` ma w Definition of Done punkt 5 „PR/MR z szablonu".
- WARN 9: `git push --dry-run` nawiązuje połączenie ze zdalnym (wykonuje negocjację), więc test bramki z zadania 3.2 realnie dotknąłby GitHuba.
- BLOCKER 1: `tasks.md` zadanie 2.1 wymienia `bash scripts/push.sh` jako przypadek przepuszczający, przy jednoczesnym wymaganiu w `spec.md` o blokadzie „niezależnie od użytego narzędzia i składni wywołania". Sprzeczność jest w literze artefaktów.
