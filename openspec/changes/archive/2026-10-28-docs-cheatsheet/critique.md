# Critique: docs-cheatsheet

Krytyk: `codex exec -m gpt-6-astra -c model_reasoning_effort=high` (wariant claude-codex).
Wejście: proposal.md, design.md, tasks.md (specs pominięte, `skip_specs: true`).
Data: 2026-10-28.

## critical

- **BLOCKER — `design.md:29`, `tasks.md:10`: brak treści, której zgodność można ocenić.** Design nakazuje użyć „dosłownie” wierszy podanych przez użytkownika, ale artefakty zawierają tylko sześć tematów. Nie definiują wywołań, argumentów ani obiecywanego zachowania. Można spełnić wszystkie sprawdzenia strukturalne, wpisując błędny proces. Dopisz wzorcowe sześć wierszy albo wymagania semantyczne dla każdego: wejście, argumenty, działanie, warunki zatrzymania i źródło potwierdzające opis. `skip_specs: true` nie zastępuje tych kryteriów.

## major

- **WARN — `tasks.md:5`: test nie sprawdza deklarowanych wartości.** Wzorzec wyszukuje cztery pola `name:`, choć zadanie wymienia osiem identyfikatorów. Nie sprawdza `systematic-debugging`, prefiksu `/ai-developer-ops:` ani wywołań `$…`. Trafienie `agents/skills` również nie dowodzi, że właściwy skill jest symlinkowany. Rozdziel weryfikację nazw skilli, namespace pluginu, instalacji i zależności Superpowers; zapisz konkretne źródło dla każdego identyfikatora. Brak trafienia powinien powodować korektę planu, nie ciche usunięcie potrzebnego wejścia.

- **WARN — `design.md:16`, `tasks.md:5`, `tasks.md:11`: sprzeczny zakres komend zewnętrznych.** Non-goal wyklucza dokumentowanie komend niedostarczanych przez repo, podczas gdy zadania wymagają dokumentowania Superpowers. Ustal wyjątek dla instalowanych zależności i rozróżnij wejścia użytkownika od wywołań wewnętrznych. Obecny zapis pozwala zarówno usunąć wymagane informacje, jak i naruszyć non-goal.

- **WARN — `proposal.md:10`, `tasks.md:10`: sytuacje nie tworzą jednoznacznej tabeli decyzyjnej.** Bug może jednocześnie być poprawką na jedno zdanie albo dużą zmianą. Brakuje pierwszeństwa reguł oraz przejścia od diagnozy do naprawy. Dopisz, że krótki opis błędu nie znosi obowiązku testu regresyjnego, oraz określ, kiedy diagnoza przechodzi do procesu OpenSpec.

- **WARN — `design.md:29`, `tasks.md:11`: wariant Codex pozostaje niekompletny.** Podane zamienniki obejmują tylko trzy skille. Nie rozwiązują wiersza o debugowaniu, sposobu zlecenia pytania o API ani różnicy `docs-researcher` / `docs_researcher`, którą wskazuje `AGENTS.md:15`. Samo istnienie instrukcji TDD nie dowodzi automatycznego uruchomienia skilla. Wymagaj sprawdzenia wszystkich sześciu wierszy dla obu wariantów, także ich zachowania i wymaganych akceptacji użytkownika.

- **WARN — `design.md:34`, `tasks.md:15`: kontrola struktury nie dowodzi poprawnego renderowania GFM.** Równa liczba separatorów i brak surowych tagów nie wykrywają choćby niezamkniętego bloku kodu przed tabelą, w którym cała tabela stanie się tekstem. Usuń deklarację wykrywania „wszystkich” awarii. Dodaj podgląd wyrenderowanego dokumentu przez parser GFM lub GitHub i kontrolę trzech kolumn, sześciu wierszy oraz widoczności placeholderów.

- **WARN — `tasks.md:18`: `git status` nie mierzy zakresu tej zmiany.** Odrzuca wcześniejsze pliki użytkownika, a pomija zmiany już zacommitowane. Aktualny workspace zawiera niezwiązane `.idea/misc.xml` i `.tmp/`, więc kryterium już jest niespełnialne bez dodatkowych działań poza zakresem. Zapisz stan początkowy i sprawdzaj diff zmiany względem ustalonej bazy, osobno uwzględniając pliki nieśledzone.

## minor

- **NOTE — `design.md:10`, `tasks.md:16`: 40 linii źródła nie oznacza czytelności bez przewijania.** Jeden bardzo długi wiersz nadal liczy się jako jedna linia. Określ szerokość podglądu i rodzaj przewijania albo usuń niemierzalną obietnicę.

- **NOTE — `design.md:33`: wskazana reguła utrzymania dokumentacji nie istnieje w przytoczonej konwencji.** „`templates/` to źródło prawdy” dotyczy kopiowanych plików, nie synchronizacji README ze skillami. Opisz ryzyko jako pozostające po jednorazowym sprawdzeniu.

## open questions

- Czy „pytanie o API” ma zawierać gotowy prompt delegujący do agenta, czy bezpośrednie wywołanie? Sam identyfikator agenta nie definiuje instrukcji do wpisania.
- Czy wiersz PR/MR opisuje publikację gotowej zmiany, czy również jej przygotowanie? Jakie warunki wejściowe musi spełniać użytkownik?
- Gdzie znajduje się treść użytkownika, do której odwołuje się decyzja 5?

**Werdykt krytyka: FAIL.**

## Uwaga do raportu krytyka

Krytyk uruchomił `make check` we własnym sandboxie i zgłosił 23 błędy. To artefakt jego środowiska (`FileNotFoundError: No usable temporary directory found` — `tests/util.py:31` woła `tempfile.mkdtemp`), nie regresja. Lokalnie `make check` jest zielone: `Ran 23 tests ... OK`, exit 0.
