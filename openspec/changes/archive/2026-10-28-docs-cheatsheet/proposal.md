# Proposal

## Why

README opisuje stos i proces abstrakcyjnie ("spec -> plan -> wykonanie -> review -> PR"), ale nie mówi, co użytkownik ma **wpisać** w konkretnej sytuacji. Nowy użytkownik ma do wyboru kilkadziesiąt komend z czterech pluginów (`ai-developer-ops`, `superpowers`, `opsx`, security) i nie wie, kiedy zacząć od `/opsx:propose`, kiedy od `/superpowers:systematic-debugging`, a kiedy po prostu poprosić. Brakuje jednej tabeli decyzyjnej: sytuacja -> komenda -> co się stanie.

## What Changes

- Nowa sekcja w `README.md`: ściągawka "według sytuacji" jako tabela Markdown z trzema kolumnami — `Sytuacja` | `Wypisujesz` | `Co się dzieje pod spodem`.
- Sześć wierszy pokrywających sytuacje: zmiana większa niż jedno zdanie, bug, review dowolnego celu, poprawka na jedno zdanie, PR/MR, pytanie o API biblioteki.
- Dwa akapity pod tabelą: (a) czego nie mieszać — jeden plan to `openspec/changes/<id>/tasks.md`, `superpowers:brainstorming` i `superpowers:writing-plans` tylko ręcznie, `ops-ship` zamiast `superpowers:finishing-a-development-branch` przy zmianie prowadzonej przez OpenSpec, plus klauzula, że bug zostaje bugiem nawet przy jednoliniowym fiksie (test odtwarzający obowiązkowy); (b) wariant Codex — bez Superpowers, proces niosą skille `ops-*` z agentami TOML, wywołania `$ops-feature`, `$ops-review`, `$ops-ship`, brak `systematic-debugging`, agent od dokumentacji nazywa się `docs_researcher` z podkreśleniem.
- Bez zmian zachowania produktu: tylko dokumentacja. Brak **BREAKING**.

Dwie ostatnie klauzule w akapitach (a) i (b) weszły po `ops-critique` (WARN 3 i WARN 4 w `critique.md`): tabela nie rozstrzyga, czy mały bug to "bug" czy "poprawka na jedno zdanie", a rozjazd `docs-researcher` / `docs_researcher` cicho zawodzi w Codex. Dosłowna treść sekcji jest zamrożona w `design.md`.

## Capabilities

### New Capabilities

Brak. Zmiana jest czysto dokumentacyjna — nie dodaje ani nie modyfikuje zachowania systemu, więc żaden spec nie powstaje ani się nie zmienia. `.openspec.yaml` tej zmiany ustawia `skip_specs: true`.

### Modified Capabilities

Brak. Projekt nie ma jeszcze żadnych speców (`openspec list --specs` → "No specs found"), a ściągawka tylko opisuje proces już zaimplementowany w `skills/ops-*/SKILL.md`, `AGENTS.md` i `scripts/`.

## Impact

- Pliki: `README.md` (jedyny plik produkcyjny w zakresie).
- Non-goals: żadnych zmian w `skills/`, `scripts/`, `templates/`, `agents/`, `codex/`, `Makefile`, `AGENTS.md`.
- Ryzyko: ściągawka, która rozejdzie się ze skillami, jest gorsza niż jej brak. Każda komenda i każda nazwa agenta w tabeli musi być zweryfikowana wobec `skills/*/SKILL.md`, `templates/agents/`, `codex/agents/` i `scripts/install.sh`. Ryzyko rozjazdu pozostaje po tej zmianie — repo nie ma mechanizmu wiążącego README ze `skills/`, a dodanie go byłoby zmianą w skryptach, czyli non-goalem.
- Bramki: `make check` (shellcheck + bash -n + jq + tomllib + unittest) nie dotyka Markdown, więc przejdzie, ale musi pozostać zielone. Render tabeli potwierdza `gh api --method POST /markdown -f mode=gfm`, czyli renderer GitHuba; limit 40 linii liczy `awk`. Oba sprawdzenia są jednorazowe i nie wchodzą do `Makefile`.
