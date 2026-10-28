# Evidence: ops-discover

Gałąź `feat/ops-discover`, worktree `.claude/worktrees/ops-discover`, baza `7afdda8`.

## make check

```
shellcheck scripts/detect.sh scripts/format-file.sh scripts/init.sh scripts/install.sh scripts/protect-paths.sh scripts/render_arch.py... (bez .py)
typecheck OK        # w tym py_compile dla 7 plików, m.in. scripts/render_arch.py
Ran 204 tests in 13.632s
OK
```

Kod wyjścia 0. Wzrost z 23 testów (baza) do 204.

## e2e

PASS. `make e2e` → `E2E_SMOKE_OK`. Smoke uruchamia `init.sh` w świeżym repo tymczasowym i wywołuje `make check` z `templates/Makefile`; nowy cel `docs-fresh` przechodzi tam cicho, bo projekt nie ma jeszcze `docs/architecture.puml` — to dowód scenariusza „Repozytorium bez diagramu".

## Dogfooding (zadania 8.1–8.2)

- `python3 scripts/render_arch.py validate --model docs/architecture.model.json` → exit 0.
- `plantuml -failfast2 -checkonly docs/architecture.puml` → exit 0 (plantuml 1.2026.8).
- `docs/ARCHITECTURE.md`: 1 nagłówek `#`, 2 nagłówki `##`, 1 osadzenie obrazu.
- Legenda: 12 wpisów na 12 uczestników, 11 ścieżek (aktor bez ścieżki), zero brakujących, zero uczestników bez wpisu, zero wpisów bez uczestnika.
- `make docs` → `docs: rendered docs/architecture.svg`; `make docs-fresh` → exit 0.
- Diagram obejrzany jako PNG: cztery boxy warstw, przebieg główny bez grupy, trzy przebiegi niezależne jako `group`.

## Determinizm (zadanie 8.3)

**Połowa potwierdzona.** Renderer na prawdziwym modelu tego repo: trzy kolejne przebiegi `render_arch.py all --preserve`, `diff` pusty za każdym razem (exit 0). Dodatkowo testy jednostkowe: przetasowany model daje bajtowo identyczne wyjście, a data i commit nie trafiają do `.puml`.

**Połowa niepotwierdzona — do decyzji użytkownika.** Kryterium „dwa uruchomienia `ops-discover` bez zmian w kodzie dają identyczny `.puml`" obejmuje też rekonesans. W tej sesji `AgentTool` był wyłączony instrukcją użytkownika („Do not call the AgentTool unless the user requested it"), więc model powstał z rekonesansu wykonanego inline przeze mnie, nie przez pięć równoległych subagentów `Explore`. Zbieżność dwóch **niezależnych przebiegów rekonesansu** nie została więc zmierzona. Zgodnie z `design.md` → decyzja 2 spec tego nie obiecuje jako SHALL; pozostaje jednorazowym dowodem, który trzeba wykonać przy pierwszym prawdziwym uruchomieniu skilla z subagentami.

## Pokrycie scenariuszy specu (zadanie 9.2)

`openspec validate ops-discover --strict` → exit 0.

Dowody ręczne (scenariusze, których nie pokrywa test automatyczny):

- „Subagent nie modyfikuje analizowanego projektu" — nie uruchomiono subagentów w tej sesji (patrz wyżej). Test `SyntheticRepo.test_synthetic_repo_writes_only_inside_docs` pokrywa stronę renderera: żaden plik poza `docs/` nie powstaje.
- „Harness ogranicza równoległość" i „Subagent obszaru zawodzi dwa razy" — zachowanie opisane w `SKILL.md`, nieweryfikowalne bez uruchomienia subagentów.
- „Gałąź domyślna jest chroniona" — zachowanie opisane w `skills/ops-feature/SKILL.md` krok 8; wymaga chronionej gałęzi, niedostępnej lokalnie.
- „Brak plantuml i brak Dockera" — pokryte testem ze stub PATH (`test_docs_warns_and_succeeds_without_plantuml_or_docker`), łącznie z asercją, że suma kontrolna nie powstaje.

## Bramka pre-push (zadanie 9.3)

PASS. Zepsuta jedna asercja w `tests/test_render_arch.py` (etykieta agregatu `integracje (4)` → `WRONG (4)`):

```
bash .githooks/pre-push  → exit 2
Ran 204 tests ... FAILED (failures=1)
make: *** [test] Error 1
```

Po przywróceniu asercji:

```
bash .githooks/pre-push  → exit 0
Ran 204 tests ... OK
```

`git status --short` nie wymienia `tests/test_render_arch.py`, czyli plik wrócił do stanu zacommitowanego.

## Etap 1 — spec (`/opsx:verify`)

36/36 zadań, wszystkie artefakty czytelne, `openspec validate --strict` exit 0. 24 wymagania ADDED, 56 scenariuszy, zero REMOVED/RENAMED. Dwie luki znalezione na tym etapie i naprawione w fix pass: brak testu dowodzącego, że renderer nie czyta treści plików (wymaganie „Model architektury jest jedynym wejściem renderera"), oraz brak egzekwowania niepustego przebiegu `main` (scenariusz „Zakres opróżniłby przebieg główny").

## review A (poprawność)

`/code-review 7afdda8..HEAD high`. **5 findings, 0 BLOCKER po adjudykacji, wszystkie naprawione.**

1. `render_arch.py:160` — `root / path` gubi lewy operand, gdy prawy jest bezwzględny, więc `path: "/etc/hosts"` przechodził kontrolę zawierania. Naprawione: odrzucenie ścieżek bezwzględnych + porównanie `resolve()` wobec `root.resolve()`.
2. i 3. `render_arch.py:34,181` — `$` z `.match()` dopuszcza końcowy `\n`; `id: "Api\n"` przechodził i rozrywał deklarację. Naprawione: `fullmatch`.
4. `render_arch.py:859` — `puml`/`all` zgłaszały błędy modelu i dopisków w dwóch turach, wbrew decyzji 6. Naprawione: jedna lista.
5. `render_arch.py:711` — podwójne liczenie `aggregate()` w `all`. **Odłożone jako minor**: ≤12 komponentów, koszt pomijalny, a przekazywanie policzonej pary do obu funkcji dokłada sprzężenie.

Recenzent sam wycofał jeden finding (wielkość liter w `MANUAL_FORBIDDEN`) po reprodukcji — linia i tak jest odrzucana przez regułę ogólną.

## review B (drugi model)

`codex exec -m gpt-6-astra -c model_reasoning_effort=high` (wariant claude-codex). **10 BLOCKER + 4 WARN zgłoszone; 9 BLOCKER potwierdzonych i naprawionych, 1 odrzucony, 4 WARN naprawione.**

Potwierdzone reprodukcją przed naprawą:
- `%breakline()` w dopisku przemycał drugą instrukcję przez kontrolę jednoliniową → nowy `MANUAL_INJECTION_RE` + zakaz dyrektyw `!`.
- `render_arch.py` ma tryb 644, a `SKILL.md` wołał go bezpośrednio → jawny `python3`, zgodnie z konwencją `bash "$ROOT/scripts/init.sh"` z `init`.
- Przepływ awansowany z `independent` na `main` gubił swoje dopiski → gałąź `main` opróżnia też własny kubełek.
- `$(SHA256) f | cut` bierze status z `cut`, więc awaria skrótu zapisywała pusty digest i meldowała sukces → nowy cel `docs-stamp` ze sprawdzeniem statusu i niepustości.
- `docs-fresh` przechodził przy usuniętym SVG → wymagane istnienie pliku.
- `all` publikowało `.puml` przed zapisem tymczasowego `.md` → oba pliki stageowane, potem dwa `rename`.
- `archive/<id>/scope.txt` — `/opsx:archive` dodaje prefiks daty → poprawione na `<YYYY-MM-DD>-<id>`.
- `--name-only` gubi źródło zmiany nazwy → dodane `--no-renames`.
- `id` z końcowym `\n` (duplikat review A).
- WARN-y: crash walidacji na `id: []`, test lokalizacji zapisu ignorujący kod wyjścia, test sierot niewykrywający niejawnych uczestników, podciągowe sprawdzenie `.PHONY`.

**Odrzucony BLOCKER** — „wyjście zależy od zegara i commita". Spec ogranicza determinizm do `docs/architecture.puml` („Renderer SHALL produkować bajtowo identyczny `docs/architecture.puml`"), a osobny scenariusz „Data i commit poza diagramem" wprost wymaga, by data i commit żyły w Markdownie. Zachowanie jest zgodne ze specem i z decyzją 2; recenzent przyjął szerszy zakres, niż spec deklaruje.

Uwaga środowiskowa: recenzent zgłosił, że `make check` przerwał się na `typecheck`, bo jego Python nie ma `tomllib`. To artefakt jego sandboxu — lokalnie `make check` jest zielone (226 testów).

## Etap docs-researcher (PlantUML)

Zweryfikowane wobec dokumentacji i empirycznie:
- `-tsvg` zapisuje obok źródła — potwierdzone.
- `-checkonly` jest przestarzałe, `-failfast2` redundantne z nim; udokumentowany jest `--check-syntax` z kontraktem kodu wyjścia. Testy przełączone.
- Wywołanie Dockera **zweryfikowane empirycznie** (dokumentacja niedostępna): `docker run --rm -v "$PWD/docs:/data" plantuml/plantuml -tsvg /data/architecture.puml` → exit 0, zapisuje `docs/architecture.svg`.
- **Wiadomość wewnątrz `box ... end box` jest tolerowana, ale nieudokumentowana.** Stąd nowa reguła: w sekcji boxa dopisek może być wyłącznie komentarzem.
- Zmierzone zachowanie `plantuml`: śmieci → 200, brak diagramu → 100, zbłąkany `end` → 200, ale niedomknięty `box`/`group` → 0. Dodany test-strażnik dowodzący, że kontrola parsowania w ogóle potrafi zawieść.

## security

PASS, zero findings. Powierzchnia: jedno wywołanie `subprocess.run(["git","rev-parse","--short","HEAD"])` — stała lista argv, bez `shell=True`, bez interpolacji. Parsowanie wyłącznie `json` ze stdlib; brak `eval`, `exec`, `pickle`, `yaml`. Zapisy ograniczone do ścieżek podanych flagami CLI (wartości zaufane). Po naprawie findingu z review A ścieżki z modelu nie mogą już wyjść poza `--root`.

## Werdykt

Po fix pass: `make check` exit 0 (226 testów), `make e2e` `E2E_SMOKE_OK`, `make docs-fresh` exit 0, `openspec validate --strict` exit 0. Zero otwartych BLOCKER. Jeden minor odłożony świadomie (podwójne `aggregate()` w `all`).
