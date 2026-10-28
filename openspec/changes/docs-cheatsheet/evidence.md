# Evidence: docs-cheatsheet

## baseline (zadanie 2.1)

`git rev-parse HEAD`:
```
7afdda8a51ed22b05356b4c5ce4e39d840ed1624
```

`git ls-files --others --exclude-standard`:
```
openspec/changes/docs-cheatsheet/.openspec.yaml
openspec/changes/docs-cheatsheet/critique.md
openspec/changes/docs-cheatsheet/design.md
openspec/changes/docs-cheatsheet/evidence.md
openspec/changes/docs-cheatsheet/handoff.md
openspec/changes/docs-cheatsheet/proposal.md
openspec/changes/docs-cheatsheet/tasks.md
```

## 3.1 pre-check struktury tabeli (zadanie 3.1)

Pre-check, NIE dowód renderu.

```
$ grep '^|' README.md | awk '{n=gsub(/\|/,"|"); print NR": "n}'
1: 4
2: 4
3: 4
4: 4
5: 4
6: 4
7: 4
8: 4
```

8 wierszy (nagłówek + separator + 6 danych), każdy z 4 pipes. **PASS.**

## 3.2 render przez renderer GitHuba (zadanie 3.2)

```
$ gh api --method POST /markdown -f mode=gfm -f "text=$(cat README.md)" > /tmp/readme-render.html
$ echo $?
0
```

Asercje na `/tmp/readme-render.html`:
```
$ grep -c '<table' /tmp/readme-render.html
1
$ grep -o '<th>' /tmp/readme-render.html | wc -l
       3
$ awk '/<tbody>/{f=1;next} /<\/tbody>/{f=0} f && /<tr>/{c++} END{print c}' /tmp/readme-render.html
6
$ grep -o '&lt;id&gt;\|&lt;cel&gt;' /tmp/readme-render.html
&lt;id&gt;
&lt;cel&gt;
&lt;cel&gt;
&lt;id&gt;
&lt;id&gt;
```

Fragment `<thead>` + pierwszy `<tr>` z `<tbody>`:
```html
<markdown-accessiblity-table><table role="table">
<thead>
<tr>
<th>Sytuacja</th>
<th>Wypisujesz</th>
<th>Co się dzieje pod spodem</th>
</tr>
</thead>
<tbody>
<tr>
<td>Zmiana większa niż jedno zdanie</td>
<td><code class="notranslate">/ai-developer-ops:ops-feature &lt;id&gt; "&lt;cel&gt;"</code></td>
<td>OpenSpec propose -&gt; <code class="notranslate">ops-critique</code> -&gt; <code class="notranslate">using-git-worktrees</code> + <code class="notranslate">subagent-driven-development</code> + TDD -&gt; <code class="notranslate">ops-review</code> -&gt; <code class="notranslate">ops-ship</code></td>
</tr>
```

`<table>` istnieje (jako `<table role="table">`), 3 `<th>`, 6 `<tr>` w `<tbody>`, placeholdery widoczne jako `&lt;id&gt;` i `&lt;cel&gt;` (escapowane — backticki zadziałały, GFM nie zjadł ich jako tagów HTML). `<target>` nie występuje w treści — to zgodne z zatwierdzoną treścią, nie błąd. **PASS.**

## 3.3 budżet 40 linii (zadanie 3.3)

```
$ awk '/^## Ściągawka/{f=1} f&&/^## Pliki/{exit} f{n++} END{print n}' README.md
15
```

15 ≤ 40. README.md nie wymaga zmian. **PASS.**

## 3.4 zakres zmiany (zadanie 3.4)

Baza: `7afdda8a51ed22b05356b4c5ce4e39d840ed1624` (sekcja `## baseline (zadanie 2.1)` powyżej).

```
$ git diff --name-only 7afdda8a51ed22b05356b4c5ce4e39d840ed1624
README.md
openspec/changes/docs-cheatsheet/evidence.md
```

```
$ git status --porcelain
?? openspec/changes/docs-cheatsheet/.openspec.yaml
?? openspec/changes/docs-cheatsheet/critique.md
?? openspec/changes/docs-cheatsheet/design.md
?? openspec/changes/docs-cheatsheet/handoff.md
?? openspec/changes/docs-cheatsheet/proposal.md
?? openspec/changes/docs-cheatsheet/tasks.md
```

```
$ git status --porcelain --ignored
 M openspec/changes/docs-cheatsheet/evidence.md
?? openspec/changes/docs-cheatsheet/.openspec.yaml
?? openspec/changes/docs-cheatsheet/critique.md
?? openspec/changes/docs-cheatsheet/design.md
?? openspec/changes/docs-cheatsheet/handoff.md
?? openspec/changes/docs-cheatsheet/proposal.md
?? openspec/changes/docs-cheatsheet/tasks.md
!! .aidevops/
!! .superpowers/
!! tests/__pycache__/
$ cat .superpowers/sdd/.gitignore
*
```

`.superpowers/` jest w całości ignorowany, bo cała jego treść leży pod `.superpowers/sdd/`, a tam jest zagnieżdżony `.superpowers/sdd/.gitignore` z regułą `*` — stąd git zwija cały katalog jako `!!` i nie pokazuje go w zwykłym `git status --porcelain`. `.tmp/` w tym worktree nie istnieje.

Obserwacja: `evidence.md` pojawia się w diffie obok `README.md`, ponieważ commit `2788470` (zadanie 2.2) utworzył `evidence.md` jako plik śledzony w tym samym commicie, w którym zapisał bazę (zadanie 2.1) — to bookkeeping evidence, nie rozrost zakresu feature'u. Żaden plik poza `{README.md, evidence.md}` nie różni się od bazy. Wszystkie nieśledzone pozycje leżą wyłącznie w `openspec/changes/docs-cheatsheet/`. `.superpowers/` jest zignorowany przez `.gitignore` (nie pojawia się nawet w zwykłym `git status --porcelain`); `.tmp/` nie istnieje w tym worktree. Nic nie zostało usunięte z `.superpowers/` ani `.tmp/`. **PASS** (z zastrzeżeniem: dosłowny zapis kryterium "wyłącznie README.md" nie uwzględnia, że `evidence.md` jest śledzonym plikiem bookkeepingu edytowanym przez każde zadanie z designu tej zmiany — patrz concern w raporcie).

## make check
```
$ make check; echo "EXIT_CODE:$?"
shellcheck scripts/detect.sh scripts/format-file.sh scripts/init.sh scripts/install.sh scripts/protect-paths.sh scripts/stop-gate.sh tests/e2e_smoke.sh .githooks/pre-push templates/pre-push
typecheck OK
/Users/wojciechwylezol/PycharmProjects/ai-developer-ops/.venv/bin/python3 -m unittest discover -s tests -t .
.......................
----------------------------------------------------------------------
Ran 23 tests in 1.295s

OK
EXIT_CODE:0
```
**PASS** (kod 0, "Ran 23 tests ... OK"). Uwaga: `make check` NIE waliduje Markdown (lintuje `*.sh`/`*.json`/`*.toml`, odpala `tests/`) — to NIE jest dowód na 3.1-3.3, tylko na gate'y shellcheck/typecheck/unittest.
## e2e
PASS/FAIL, kroki, screenshoty
## review A (poprawność)
PASS/FAIL, liczba BLOCKER/WARN
## review B (drugi model)
PASS/FAIL, liczba BLOCKER/WARN
## security
PASS/FAIL

## review A (poprawność) — /code-review main...HEAD high
7 findings, wszystkie przejrzane wobec HEAD po fiksie BLOCKERA z review B.
Werdykt wejściowy: FAIL. Po poprawkach: PASS.

WARN 1 (evidence.md:130) — 3.4 oznaczone PASS, choć evidence mówiło wprost, że
scratch nie został usunięty, a `tasks.md:24` wymieniał usunięcie jako część
warunku PASS. Zasadne: wewnętrzna sprzeczność artefaktów. Fix: scratch usunięty,
sekcja zakresu niżej odtworzona.

WARN 2 (README.md:35) — `use docs-researcher: ...` nie jest udokumentowaną składnią
wywołania subagenta. Zasadne i istotne, bo kolumna nazywa się "Wypisujesz".
Ustalenie właściwej formy zajęło dwa podejścia, oba zapisane, bo pierwsze było błędne:
  1. Agent `claude-code-guide` odpowiedział, że poprawna forma to `@<nazwa>`, czyli
     `@docs-researcher`. Wprowadziłem to w commicie 6248c6e.
  2. Powtórzone review B (Codex) zgłosiło to jako BLOCKER: w Claude Code 2.1.251
     `@docs-researcher` parsuje się jako wzmianka o *pliku*, a ręczna forma to
     `@agent-<nazwa>`.
  3. Rozstrzygnięte wobec źródła, nie przez wybór strony — `code.claude.com/docs/en/
     sub-agents.md` podaje formę ręczną `@agent-<name>` i wprost mówi, że przy formie
     bez prefiksu "the typeahead shows file matches rather than agents". Bare `@name`
     nie jest pokazane jako poprawne dla subagentów.
Codex miał rację, `claude-code-guide` się mylił. Fix: `@agent-docs-researcher <pytanie>`.
Lekcja: raport subagenta to niezweryfikowane twierdzenie, także gdy brzmi
autorytatywnie i cytuje URL. Dopiero pobranie dokumentacji zamknęło sprawę.

WARN 3 (README.md:39) — akapit o Codeksie mówił, czego nie ma, bez zamiennika dla
wiersza "Bug". Zasadne; to niedomknięta część WARN 4 z `critique.md`.
Fix: akapit (b) wskazuje teraz `AGENTS.md` (najpierw test odtwarzający) i agenta
`tester` jako ścieżkę w Codeksie.

WARN 4 (README.md:32) — kolizja placeholderów: `<cel>` w wierszu 1 znaczy "cel
zmiany" (tekst swobodny), a w wierszu 3 "cel review" (PR/gałąź/zakres/ścieżka).
Zasadne. Fix: wiersz 3 używa `<target>`, dokładnie tak jak `argument-hint`
w `skills/ops-review/SKILL.md`. Po fiksie `<cel>` występuje raz, w jednym znaczeniu.

NOTE 5 (README.md:30) — kolumna 3 wiersza 1 opisuje ten sam przepływ co `## Proces`.
Częściowo zasadne. Kolumna 3 jest wymagana zakresem zmiany, a `## Proces` jest prozą
bez nazw skilli — inna wysokość lotu. Odrzucam zmianę deliverable'a; poprawiam
natomiast zbyt szeroko sformułowany non-goal w `design.md`, który sam sobie przeczył.
Pozostaje przyjęty koszt: przy zmianie cyklu `ops-feature` odświeżyć oba miejsca.

NOTE 6 (design.md:72) — brak automatycznej ochrony przed rozjazdem README ze
skillami. Zasadne i już udokumentowane jako ryzyko rezydualne; domknięcie wymaga
testu w `tests/`, czyli non-goalu. Bez zmian, świadomie.

ODRZUCONE (handoff.md:4) — "cztery etapy" miało być nieprawdą przy `skip_specs`.
Nie zgadzam się: `skills/ops-review/SKILL.md` wiąże etap 1 z istnieniem *spec folderu*
(`openspec/changes/docs-cheatsheet/`), który istnieje, i etap 1 faktycznie się wykonał
(`/opsx:verify` → 13/13 zadań, design adherence 6/6, checki spec-zależne Not applicable
z racji `skip_specs`). Cztery etapy przebiegły. Słuszna była natomiast obserwacja, że
`evidence.md` nie miało wyniku etapu 1 — uzupełnione sekcją niżej.

## etap 1 (spec) — /opsx:verify docs-cheatsheet
Completeness: 13/13 zadań (`taskTrackingConfigured: true`, `remaining: 0`,
`unavailableTrackingFiles: null`, state `all_done`). Spec Coverage: Not applicable
(`specs` ma status `skipped` przez `skip_specs: true`).
Correctness: Not applicable (zero requirementów ADDED/MODIFIED).
Coherence: Design Adherence 6/6 decyzji potwierdzonych; Code Pattern Consistency bez
odchyleń (polska proza + dosłowne identyfikatory, `->` jak w `README.md:24`, poziom `##`).
Werdykt: PASS, 0 BLOCKER, 0 WARN.

## review B (drugi model) — codex adversarial-review --base main
Model: Codex (gpt-6.1-sol), inny niż autor (Claude Opus 5). Werdykt wejściowy: FAIL / needs-attention.

BLOCKER (README.md:31) — "Review the complete bug fix":
przy przepisie `ops-review HEAD~1..HEAD` niezacommitowany fix zostaje całkowicie
nieprzejrzany (zakres wskazuje poprzedni commit), a przy fiksie wielocommitowym
wcześniejsze commity wypadają z review. `skills/ops-review/SKILL.md:7` przekazuje
zakres dosłownie, więc nie ma siatki bezpieczeństwa.

Potwierdzenie na żywo (nie przyjęte na słowo):
    $ git status --porcelain
     M openspec/changes/docs-cheatsheet/tasks.md
    $ git diff --name-only HEAD~1..HEAD
    openspec/changes/docs-cheatsheet/.openspec.yaml
    openspec/changes/docs-cheatsheet/critique.md
    openspec/changes/docs-cheatsheet/design.md
    openspec/changes/docs-cheatsheet/handoff.md
    openspec/changes/docs-cheatsheet/proposal.md
    openspec/changes/docs-cheatsheet/tasks.md
Niezacommitowana zmiana w tasks.md nie trafia do zakresu HEAD~1..HEAD — review
przeszłoby bez spojrzenia na nią.

Luka w mojej weryfikacji: zadanie 1.5 potwierdziło, że `ops-review` *przyjmuje*
zakresy `A..B` (składnia), ale nie pytało, czy `HEAD~1..HEAD` jest *właściwym*
zakresem dla przepisu na buga (semantyka). Etap 4 (drugi model) wyłapał to, czego
etapy 1-3 nie szukały.

Fix: wiersz 2 tabeli mówi teraz `/ai-developer-ops:ops-review <zakres fiksa>`,
a kolumna 3 dodaje warunek: "`HEAD~1..HEAD` dopiero gdy cały fix siedzi w ostatnim
commicie". Poprawione w `design.md` (zamrożone źródło) i w `README.md`.

Uwaga do raportu Codexa: jego `make check` padł (exit 2) z powodu sandboxu bez
zapisywalnego katalogu tymczasowego — `tests/util.py:31` woła `tempfile.mkdtemp`.
To artefakt środowiska krytyka, nie regresja. Lokalnie exit 0, 23 testy OK.

## security
Zakres zmiany: 7 plików Markdown + 3-linijkowy YAML (`skip_specs: true`). Zero kodu
wykonywalnego, zero skryptów, zero CI, zero manifestów zależności.
Sprawdzone: dodane linie README bez wzorców `curl|wget|sudo|rm -rf|eval|chmod|base64`
i bez słów `token|secret|password|api_key` (zero trafień); sześć komend z kolumny 2 to
slash-commandy Claude/Codex albo prośba w języku naturalnym, nie komendy shella; nowy
tekst nie osłabia bramek repo (opisuje `make check` i hooki jako wiążące).
Werdykt: PASS, 0 BLOCKER, 0 WARN. Powierzchnia ataku tej zmiany jest pusta
z konstrukcji — to wynik zakresowania, nie głębokiej analizy.

## ponowna weryfikacja kryteriów po fiksie BLOCKERA
    $ diff <frozen design.md> <sekcja README.md>   -> IDENTICAL
    $ grep '^|' README.md | awk '{n=gsub(/\|/,"|"); print NR": "n}'
    1..8: po 4 pipes
    $ awk '/^## Ściągawka/{f=1} f&&/^## Pliki/{exit} f{n++} END{print n}' README.md
    15          (budżet 40)
    $ gh api --method POST /markdown -f mode=gfm -f "text=$(cat README.md)"
    <th> x3, <tr> w <tbody> x6, placeholdery: &lt;id&gt; x3, &lt;cel&gt; x2,
    &lt;zakres fiksa&gt; x1 — wszystkie zescapowane, żaden nie zjedzony jako tag HTML
    $ make check
    exit=0, Ran 23 tests ... OK
    $ make e2e
    exit=0, E2E_SMOKE_OK

## ponowna weryfikacja po fiksach z review A
    $ diff <frozen design.md> <sekcja README.md>   -> IDENTICAL
    $ awk '/^## Ściągawka/{f=1} f&&/^## Pliki/{exit} f{n++} END{print n}' README.md
    15          (budżet 40)
    $ grep '^|' README.md | awk '{n=gsub(/\|/,"|"); print NR": "n}'
    1..8: po 4 pipes
    $ gh api --method POST /markdown -f mode=gfm -f "text=$(cat README.md)"
    <th> x3, <tr> w <tbody> x6
    placeholdery zescapowane: &lt;id&gt; x3, &lt;cel&gt; x1, &lt;target&gt; x1,
    &lt;pytanie&gt; x1, &lt;zakres fiksa&gt; x1
    (&lt;projekt&gt; x2 to istniejąca treść README, nie ta zmiana)
    kolizja `<cel>` zamknięta: występuje raz, w jednym znaczeniu
    $ make check
    exit=0, Ran 23 tests ... OK

## zakres końcowy (zadanie 3.4, odtworzone po usunięciu scratchu)
    $ git diff --name-only 7afdda8a51ed22b05356b4c5ce4e39d840ed1624
    README.md
    openspec/changes/docs-cheatsheet/.openspec.yaml
    openspec/changes/docs-cheatsheet/critique.md
    openspec/changes/docs-cheatsheet/design.md
    openspec/changes/docs-cheatsheet/evidence.md
    openspec/changes/docs-cheatsheet/handoff.md
    openspec/changes/docs-cheatsheet/proposal.md
    openspec/changes/docs-cheatsheet/tasks.md
`README.md` jest jedynym plikiem produkcyjnym; pozostałe to artefakty tej zmiany.
Scratch (`.superpowers/`) usunięty — warunek z `tasks.md:24` spełniony realnie,
nie tylko zadeklarowany. `.tmp/` nigdy nie istniał w tym worktree (był w głównym
checkoucie). `.idea/misc.xml` nietknięty.
