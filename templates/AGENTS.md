# <repo> — instrukcje dla agentów (Claude Code czyta ten plik natywnie; Codex też)

## Komendy
- Bramka: `make check` (lint + typecheck + testy). Przed "done" zawsze.
- Jeden test: TODO
- E2E / smoke: `make e2e`

## Proces
- Spec i plan: OpenSpec. Zmiana większa niż jedno zdanie zaczyna się od `/opsx:propose`. Plan to `openspec/changes/<id>/tasks.md`. Nie twórz drugiego planu.
- Jedno zadanie = jeden świeży kontekst. TDD: test czerwony -> kod -> zielony -> refactor.
- Bug: najpierw test odtwarzający błąd. Fix bez testu regresyjnego nie istnieje.
- Nie refaktoruj poza zakresem zadania. Migracje, lockfile'y, CI: tylko za zgodą użytkownika.
- Dowody, nie deklaracje: wynik `make check` do `openspec/changes/<id>/evidence.md` i do PR/MR. Dotyczy też zdań typu "usunięte", "sprawdzone", "zrobione" — wklej wyjście komendy albo nie pisz werdyktu.
- Weryfikacja składni to nie weryfikacja semantyki. To, że narzędzie przyjmuje argument, nie znaczy, że to właściwy argument: `ops-review` przyjmuje `HEAD~1..HEAD`, ale ten zakres gubi niezacommitowany fix; `@nazwa` jest poprawnym mentionem — pliku, nie agenta (agent to `@agent-nazwa`). Sprawdzaj, co komenda robi, nie czy się parsuje.
- Przekazanie między narzędziami: `openspec/changes/<id>/handoff.md` (owner, status, next_action).
- Przed planowaniem przeczytaj `docs/ARCHITECTURE.md`. Nieaktualność zgłoś w raporcie, nie poprawiaj diagramu w trakcie zadania — aktualizuje go wyłącznie `ops-discover`.
- Przed użyciem API zewnętrznej biblioteki sprawdź dokumentację jej wersji z lockfile'a przez agenta docs-researcher (Codex: docs_researcher). Nie zgaduj sygnatur. Najpierw llms.txt dostawcy, potem Context7.

## Format review (obowiązuje każdy review, także /code-review i codex review)
BLOCKER / WARN / NOTE z `plik:linia`. Na końcu werdykt: PASS albo FAIL. Tylko poprawność i wymagania. Bez uwag o stylu.

## Definition of Done
1. `make check` zielone. 2. Review bez BLOCKER. 3. evidence.md uzupełnione. 4. Spec zgodny z kodem (`/opsx:verify`). 5. PR/MR z szablonu.

## Konwencje
- Gałęzie: feat/<id>, fix/<id>. Commity: Conventional Commits.
- TODO: styl kodu, pułapki, architektura (max 20 linii)
