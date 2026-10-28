# Proposal

## Why

Rekonesans projektu jest dziś krokiem 3 w `skills/init/SKILL.md` ("Write docs/ARCHITECTURE.md, max 2 pages") i kończy się prozą, której nikt nie odświeża. Efekt widać w tym repo: `docs/ARCHITECTURE.md` ma 82 linie tekstu, powstał raz przy inicjalizacji i nie ma żadnej bramki pilnującej zgodności z kodem. Agent wchodzący w zadanie musi albo przeczytać dwie strony prozy, albo zrobić rekonesans od nowa — za każdym razem, w każdym świeżym kontekście. Brakuje jednego artefaktu, który pokazuje architekturę jako obraz, da się odświeżyć mechanicznie po każdej zmianie i ma bramkę wykrywającą, że obraz rozszedł się ze źródłem.

## What Changes

- Nowy skill `skills/ops-discover/SKILL.md`: rekonesans równoległymi subagentami read-only (Claude: `Explore`, Codex: `explorer`) po pięciu obszarach — punkty wejścia, komponenty i odpowiedzialności, przepływ danych, integracje zewnętrzne, zadania w tle.
- Rekonesans zapisuje fakty do `docs/architecture.model.json` (komponenty, warstwy, interakcje, ścieżki plików). Nowy skrypt `scripts/render_arch.py` renderuje z tego modelu deterministycznie `docs/architecture.puml` oraz `docs/ARCHITECTURE.md`. Model jest jedynym wejściem renderera; renderer nie interpretuje kodu.
- `docs/ARCHITECTURE.md` zmienia formę z prozy na plik wizualny o dokładnie czterech częściach: tytuł, osadzony obraz `docs/architecture.svg`, `## Legenda uczestników` (jedna linia na komponent z odwołaniem do istniejącego pliku lub katalogu), `## Ostatnia aktualizacja` (data, zakres, commit). **BREAKING** dla treści tego pliku — dotychczasowa proza przestaje istnieć (zostaje w historii gita).
- Jeden diagram sekwencji PlantUML: uczestnicy to komponenty (API, serwisy, repozytoria, baza, kolejka, cache, integracje, UI), nigdy klasy ani funkcje; warstwy grupowane przez `box`; główny przebieg od wejścia użytkownika do odpowiedzi; przebiegi niezależne (joby, webhooki) jako `group` w tym samym diagramie; każda strzałka opisana czasownikiem i nazwą operacji; stała kolejność (warstwa, potem alfabetycznie); max 12 uczestników, nadmiar agregowany.
- Flaga `--refresh`: ponowny rekonesans dodaje nowe komponenty i interakcje, usuwa nieistniejące, zachowuje ręczne dopiski oznaczone komentarzem `' manual`.
- Flaga `--scope <ścieżki>`: ogranicza rekonesans do podanych ścieżek.
- Flaga `--onboarding`: dodatkowo `docs/ONBOARDING.md` — uruchomienie lokalne, kolejność czytania plików, 5 ścieżek wykonania z odwołaniem do uczestników diagramu, 10 pytań z odpowiedziami i odwołaniami do plików, max 4 strony.
- Nowe cele w `templates/Makefile` i w kopii w korzeniu repo: `docs` renderuje SVG z `.puml` (lokalny `plantuml`, w razie braku `docker run plantuml/plantuml`) i zapisuje `docs/architecture.svg.sha256`; `check` zyskuje `docs-fresh`, który porównuje sumę kontrolną `.puml` z tym zapisem. Krok jest bez efektu, gdy `.puml` nie istnieje, żeby nie psuć bramki w repo bez diagramu.
- `make typecheck` **w tym repo** zyskuje kompilację `*.py`, bo `scripts/render_arch.py` jest pierwszym produkcyjnym skryptem w Pythonie. Krok nie wchodzi do `templates/Makefile` — gatuje nasz renderer, nieobecny w projektach docelowych.
- Integracje: `skills/init/SKILL.md` krok 3 wywołuje `ops-discover --onboarding` zamiast własnego opisu rekonesansu; `skills/ops-ship/SKILL.md` zapisuje `openspec/changes/<id>/scope.txt` przed pushem; `skills/ops-feature/SKILL.md` krok 8 po `/opsx:archive` wywołuje `ops-discover --refresh --scope` z tego pliku i commituje odświeżone dokumenty; `templates/AGENTS.md` zyskuje linię: przed planowaniem przeczytaj `docs/ARCHITECTURE.md`, nieaktualność zgłoś w raporcie, nie poprawiaj w trakcie zadania — aktualizacją zajmuje się wyłącznie `ops-discover`.
- To repo dogfooduje skill: `docs/ARCHITECTURE.md`, `docs/architecture.puml`, `docs/architecture.svg` i `docs/architecture.model.json` powstają przez uruchomienie `ops-discover` na samym `ai-developer-ops`.

## Capabilities

### New Capabilities

- `architecture-discovery`: rekonesans repozytorium i utrzymanie jednego wizualnego artefaktu architektury — zakres i podział rekonesansu, format modelu, deterministyczne renderowanie diagramu i legendy, semantyka odświeżania z zachowaniem ręcznych dopisków, bramki renderu oraz opcjonalny dokument onboardingowy.

### Modified Capabilities

Brak. Projekt nie ma jeszcze żadnych speców (`openspec list --specs` → "No specs found"), więc zmiany w `skills/init`, `skills/ops-feature` i `templates/AGENTS.md` nie modyfikują istniejących wymagań — wchodzą jako wymagania integracyjne do nowej capability.

## Impact

- Nowe pliki: `skills/ops-discover/SKILL.md`, `scripts/render_arch.py`, `tests/test_render_arch.py`, `docs/architecture.model.json`, `docs/architecture.puml`, `docs/architecture.svg`, `docs/architecture.svg.sha256`.
- Zmieniane pliki: `docs/ARCHITECTURE.md` (nowa forma), `templates/Makefile` + `Makefile` (cele `docs` i `docs-fresh`; `py_compile` w `typecheck` tylko w korzeniu), `templates/AGENTS.md` + `AGENTS.md` (jedna linia), `skills/init/SKILL.md` (kroki 3 i 7), `skills/ops-ship/SKILL.md` (zapis `scope.txt`), `skills/ops-feature/SKILL.md` (krok 8), `tests/util.py` (helpery fikstur).
- Poza zakresem: `README.md` — wiersz w ściągawce należy do zmiany `docs-cheatsheet`, która jest w toku i edytuje ten sam fragment.
- Zależności: `plantuml` lokalnie albo `docker` — obie opcjonalne. Brak `plantuml` i brak `docker` degraduje `make docs` do ostrzeżenia, zgodnie z konwencją "kroki opcjonalne warn-and-continue" z `AGENTS.md`. `python3` jest już twardą zależnością (`Makefile`, `tests/`).
- Rejestracja skilla jest automatyczna: `scripts/install.sh` symlinkuje `skills/*/` do `~/.agents/skills/`, a plugin Claude odkrywa `skills/` z korzenia — żaden manifest nie wymaga edycji.
- Ryzyko: diagram, który rozejdzie się z kodem, jest gorszy niż jego brak. Dlatego źródłem prawdy jest model JSON, renderer jest deterministyczny i testowany, a `make check` wykrywa nieodświeżony SVG. Rozjazdu model-kod żadna bramka nie wykryje — za to odpowiada `--refresh` wołany z `ops-feature` po archiwizacji.
- Non-goals: żadnych zmian w kodzie analizowanego projektu, żadnej dokumentacji bibliotek, żadnego drugiego diagramu.
