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

## review A (poprawność)

<uzupełnić: ops-review>

## review B (drugi model)

<uzupełnić: ops-review>

## security

<uzupełnić: ops-review>
