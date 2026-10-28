# ADR 0001: Architektura jako model JSON plus deterministyczny renderer

- Status: zaakceptowana
- Data: 2026-10-28
- Zmiana: `ops-discover` (`openspec/changes/ops-discover/`)

## Kontekst

Dokumentacja architektury pisana prozą przez agenta gnije: `docs/ARCHITECTURE.md` powstał raz przy `init` i nie miał bramki pilnującej zgodności z kodem. Chcieliśmy artefaktu wizualnego, odświeżanego mechanicznie po każdej zmianie, z kryterium: dwa uruchomienia bez zmian w kodzie dają identyczny diagram.

Naturalne podejście — niech model językowy napisze `.puml` wprost, trzymając się reguł w prompcie — nie daje tego kryterium. Reguły w prompcie są konwencją, nie gwarancją, a `make check` nie ma czego sprawdzić.

## Decyzja

Rozdzielamy ustalanie faktów od ich formatowania.

1. Rekonesans (równoległe subagenty read-only) zapisuje wyłącznie **fakty** do `docs/architecture.model.json`: komponenty z warstwą i ścieżką, przepływy, interakcje z numerem porządkowym.
2. `scripts/render_arch.py` jest **czystą funkcją modelu** i wytwarza `docs/architecture.puml` oraz `docs/ARCHITECTURE.md`. Każda decyzja o kolejności, grupowaniu i agregacji nadmiaru należy do renderera, nie do rekonesansu.
3. `.puml` nie zawiera daty ani commita — te żyją tylko w `## Ostatnia aktualizacja` w `ARCHITECTURE.md`.
4. Model ma zamknięty słownik warstw i wzorce identyfikatorów; renderer odrzuca model niespełniający schematu i nie dotyka plików wyjściowych.

Konsekwencja dla kryterium determinizmu: rozdzielamy je na dwa wymagania. Determinizm renderera jest SHALL dowodzonym testem (przetasowany model daje bajtowo to samo wyjście). Stabilność rekonesansu nie jest gwarantowana przez nic uruchamialnego w `make check`, więc SHALL-em są reguły, które ją wymuszają, a zgodność dwóch przebiegów jest jednorazowym dowodem w `evidence.md`.

## Rozważone alternatywy

**Model językowy pisze `.puml` wprost, reguły w prompcie.** Odrzucona: kryterium determinizmu stałoby się niesprawdzalne, a każda reguła formatowania byłaby egzekwowana tylko dobrą wolą. Zysk — brak nowego skryptu i brak Pythona w `scripts/` — nie pokrywa tej straty.

**Renderer w bashu z `jq`.** Odrzucona: sortowanie wielokluczowe, grupowanie i atrybucja dopisków do sekcji w bashu 3.2 bez tablic asocjacyjnych (konwencja z `AGENTS.md`) byłyby trudniejsze do przetestowania niż sam problem. `python3` jest już twardą zależnością (`Makefile`, `tests/`).

**Dwa artefakty: diagram i proza obok niego.** Odrzucona: proza i tak rozeszłaby się z diagramem, a non-goal mówi o jednym diagramie i jednym pliku wizualnym. Wiedza, której diagram nie wyraża, idzie do `AGENTS.md` (Konwencje) i do kolejnych ADR.

## Skutki

- `scripts/` przestaje być katalogiem wyłącznie bashowym. `make typecheck` w tym repo zyskuje `py_compile` po `git ls-files '*.py'`; krok świadomie **nie** wchodzi do `templates/Makefile`, bo gatuje nasz renderer, a nie projekt docelowy. To wyjątek od konwencji „`templates/` to źródło prawdy" i dlatego jest zapisany tutaj.
- Rekonesans nie może już dopisać czegoś wprost do diagramu. Ręczne dopiski mają zamkniętą składnię (wiadomość, nota, komentarz) i wracają przez `--preserve`; dopisek bez swojej sekcji wraca zakomentowany, żeby nie mógł utworzyć uczestnika poza legendą.
- Zgodność obrazu ze źródłem pilnuje suma kontrolna w `docs/architecture.svg.sha256`, nie czas modyfikacji — git nie przywraca `mtime`, więc po klonie przestarzały SVG przechodziłby bramkę opartą na czasie.
- Rozjazdu model-kod nie wykrywa żadna bramka. Odpowiada za niego `ops-discover --refresh` wołany z kroku 8 `ops-feature` po archiwizacji zmiany, z zakresem zapisanym przed scaleniem.
