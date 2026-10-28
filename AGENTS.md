# ai-developer-ops — instrukcje dla agentów (Claude Code czyta ten plik natywnie; Codex też)

## Komendy
- Bramka: `make check` (lint + typecheck + testy). Przed "done" zawsze.
- Jeden test: `python3 -m unittest tests.test_init -k <wzorzec>` (moduły: test_detect, test_init, test_hooks)
- E2E / smoke: `make e2e` (init.sh w świeżym repo tymczasowym)

## Proces
- Spec i plan: OpenSpec. Zmiana większa niż jedno zdanie zaczyna się od `/opsx:propose`. Plan to `openspec/changes/<id>/tasks.md`. Nie twórz drugiego planu.
- Jedno zadanie = jeden świeży kontekst. TDD: test czerwony -> kod -> zielony -> refactor.
- Bug: najpierw test odtwarzający błąd. Fix bez testu regresyjnego nie istnieje.
- Nie refaktoruj poza zakresem zadania. Migracje, lockfile'y, CI: tylko za zgodą użytkownika.
- Dowody, nie deklaracje: wynik `make check` do `openspec/changes/<id>/evidence.md` i do PR/MR.
- Przekazanie między narzędziami: `openspec/changes/<id>/handoff.md` (owner, status, next_action).
- Przed planowaniem przeczytaj `docs/ARCHITECTURE.md`. Nieaktualność zgłoś w raporcie, nie poprawiaj diagramu w trakcie zadania — aktualizuje go wyłącznie `ops-discover`.
- Przed użyciem API zewnętrznej biblioteki sprawdź dokumentację jej wersji z lockfile'a przez agenta docs-researcher (Codex: docs_researcher). Nie zgaduj sygnatur. Najpierw llms.txt dostawcy, potem Context7.

## Format review (obowiązuje każdy review, także /code-review i codex review)
BLOCKER / WARN / NOTE z `plik:linia`. Na końcu werdykt: PASS albo FAIL. Tylko poprawność i wymagania. Bez uwag o stylu.

## Definition of Done
1. `make check` zielone. 2. Review bez BLOCKER. 3. evidence.md uzupełnione. 4. Spec zgodny z kodem (`/opsx:verify`). 5. PR/MR z szablonu.

## Konwencje
- Gałęzie: feat/<id>, fix/<id>. Commity: Conventional Commits.
- Bash: `set -euo pipefail`; zgodność z bash 3.2 (macOS) — bez mapfile i tablic asocjacyjnych.
- `templates/` to źródło prawdy; Makefile/AGENTS.md/CI/hook w korzeniu to kopie z init.sh (dogfooding). Zmianę wprowadź w templates/, potem odśwież kopię.
- Idempotencja: `cp_if_absent` nigdy nie nadpisuje plików użytkownika; handoff.md i evidence.md w .aidevops/templates/ są nadpisywane celowo przy każdym init.
- Hooki Claude (scripts/{protect-paths,stop-gate,format-file}.sh): exit 2 = block + komunikat na stderr; format-file nigdy nie blokuje. Pułapka: protect-paths przepuszcza, gdy brak jq.
- Skrypty: twardy fail tylko dla prerekwizytów (git, npm); kroki opcjonalne warn-and-continue.
- Lint: shellcheck czysty. Format .sh: `make fmt-file FILE=<plik>` (shfmt).
- Testy: python unittest + subprocess; PATH zawężony do stubów + /usr/bin:/bin, żeby wariant (claude/codex) i host były deterministyczne.
