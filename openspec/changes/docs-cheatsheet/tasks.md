# Tasks

Treść sekcji jest zamrożona w `design.md` → "Treść do wstawienia (dosłownie)". Wstawiasz ten blok, nie redagujesz go od nowa.

## 1. Weryfikacja identyfikatorów przed pisaniem

- [x] 1.1 Potwierdzić nazwy skilli `ops-*` i agenta `docs-researcher`. Weryfikacja: `grep -rn '^name: ' skills/*/SKILL.md templates/agents/*.md` zwraca dokładnie `ops-critique`, `ops-feature`, `ops-review`, `ops-ship`, `init` oraz `docs-researcher`. Każda z pięciu nazw użytych w sekcji musi być na tej liście.
- [x] 1.2 Potwierdzić namespace `/ai-developer-ops:`. Weryfikacja: `jq -r .name .claude-plugin/plugin.json` daje `ai-developer-ops`, a `ls skills/` pokazuje katalogi skilli w korzeniu pluginu — razem dają formę `/ai-developer-ops:<skill>`.
- [x] 1.3 Potwierdzić formę `$ops-*` dla Codex oraz nazwy agentów TOML. Weryfikacja: `grep -n 'agents/skills' scripts/install.sh` pokazuje pętlę `for s in "$ROOT"/skills/*/` z `link_file "${s%/}" ~/.agents/skills/"$(basename "$s")"` (czyli symlinkowane są wszystkie skille, w tym `ops-*`), a `ls codex/agents/` zwraca `docs_researcher.toml`, `explorer.toml`, `reviewer.toml`, `tester.toml`, `worker.toml` — podkreślenie w `docs_researcher` jest celowe i musi trafić do akapitu (b).
- [x] 1.4 Potwierdzić, że sześć nazw skilli Superpowers użytych w sekcji istnieje w zainstalowanej wersji: `systematic-debugging`, `brainstorming`, `writing-plans`, `using-git-worktrees`, `subagent-driven-development`, `finishing-a-development-branch`. Weryfikacja: `grep -n 'superpowers superpowers-marketplace' scripts/install.sh` potwierdza, że plugin jest instalowany, a `ls ~/.claude/plugins/cache/superpowers-marketplace/superpowers/*/skills/` zawiera katalog dla każdej z sześciu nazw.
- [x] 1.5 Potwierdzić, że `/ai-developer-ops:ops-review` przyjmuje zakres commitów i ścieżkę (wiersze 2 i 3 tabeli). Weryfikacja: `grep -n 'argument-hint\|A\.\.B' skills/ops-review/SKILL.md` pokazuje `argument-hint: <target>` oraz regułę normalizacji `A..B`, branch, path.
- [x] 1.6 Jeśli którekolwiek sprawdzenie z 1.1–1.5 nie trafi: zatrzymać się i zaraportować użytkownikowi rozbieżność nazwy. Nie usuwać wiersza z tabeli i nie podmieniać identyfikatora samodzielnie — wiersz niesie wymaganą informację, a rozbieżność jest sygnałem o stanie repo. Weryfikacja: albo wszystkie sprawdzenia trafiły, albo istnieje raport dla użytkownika i zadanie 2 nie zostało rozpoczęte.

## 2. Sekcja w README.md

- [x] 2.1 Zapisać bazę do pomiaru zakresu: `git rev-parse HEAD` oraz listę plików nieśledzonych przed edycją (`git ls-files --others --exclude-standard`). Weryfikacja: oba wyniki są zapisane w `openspec/changes/docs-cheatsheet/evidence.md` przed pierwszą edycją `README.md`.
- [x] 2.2 Wstawić do `README.md` blok z `design.md` → "Treść do wstawienia (dosłownie)" dosłownie, bezpośrednio po sekcji `## Proces` i przed `## Pliki` (decyzja 2). Weryfikacja: blok zamrożony wyciąga `awk '/^```markdown$/{f=1;next} f&&/^```$/{exit} f' openspec/changes/docs-cheatsheet/design.md` (14 linii, sprawdzone); sekcję z README wyciąga `sed -n '/^## Ściągawka/,/^## Pliki/p' README.md | sed '$d' | sed '$d'` (dwa osobne `sed` zamiast `-e '$d' -e '/^$/{$d}'` — ta druga forma nie działa na BSD sed z macOS, a `AGENTS.md` wymaga zgodności z macOS). `diff` obu wyjść jest pusty, a `grep -c '^## ' README.md` daje 6 (było 5).

## 3. Kryteria akceptacji

- [x] 3.1 Pre-check struktury tabeli: wiersz nagłówka, wiersz separatora i wszystkie wiersze danych mają tę samą liczbę niezescapowanych `|`. Weryfikacja: skrypt ad hoc (`python3 -c ...`, bez dodawania celu do `Makefile`) wypisuje 4 dla każdego z 8 wierszy tabeli (`| A | B | C |` ma 4 pipes). To tani pre-check, nie dowód renderu (decyzja 4).
- [x] 3.2 Render przez renderer GitHuba (dowód kryterium "tabela renderuje się w GitHub"). Weryfikacja: `gh api --method POST /markdown -f mode=gfm -f "text=$(cat README.md)"` zwraca HTML, w którym istnieje `<table>` z trzema `<th>` i sześcioma `<tr>` w `<tbody>`, a placeholdery są widoczne jako `&lt;id&gt;` i `&lt;cel&gt;` (nie zjedzone jako tagi HTML). To jedyne dwa placeholdery w zatwierdzonej treści — `<target>` w niej nie występuje. Wyjście `gh` zapisane do `evidence.md`.
- [x] 3.3 Budżet 40 linii źródła: długość sekcji od `## Ściągawka według sytuacji` do następnego `## ` (wyłącznie). Weryfikacja: `awk '/^## Ściągawka/{f=1} f&&/^## Pliki/{exit} f{n++} END{print n}' README.md` ≤ 40. Jeśli próg pęknie, skrócić kolumnę 3, nie usuwać wiersza.
- [x] 3.4 Zakres zmiany wobec bazy z 2.1 (decyzja 6). Weryfikacja: `git diff --name-only <baza>` wymienia `README.md` jako jedyny plik produkcyjny, a poza nim wyłącznie pliki w `openspec/changes/docs-cheatsheet/` (`evidence.md` zmienia się z obowiązku — `AGENTS.md` wymaga dowodów w tym pliku); nowe pliki nieśledzone względem listy z 2.1 mieszczą się wyłącznie w `openspec/changes/docs-cheatsheet/`; scratch jest usunięty (`rm -rf .tmp .superpowers`), a `.idea/misc.xml` pozostaje nietknięty, bo istniał przed startem (uwaga: `.idea/` i `.tmp/` są w głównym checkoucie, nie w worktree).
- [x] 3.5 Uruchomić `make check` i dopełnić `evidence.md`. Weryfikacja: `make check` kończy się kodem 0 (`Ran 23 tests ... OK`), a `evidence.md` ma wypełnione sekcje `## make check` oraz wyniki 3.1–3.4. Uwaga: `make check` nie waliduje Markdown, więc sam w sobie nie jest dowodem na 3.1–3.3.

## Workflow follow-up

- Review: `ops-review docs-cheatsheet`; właściciel naprawia każdy BLOCKER i WARN, potem powtarza do PASS.
- Ship: `ops-ship docs-cheatsheet`. Merge zatwierdza człowiek.
- Po merge: `/opsx:archive docs-cheatsheet`.
