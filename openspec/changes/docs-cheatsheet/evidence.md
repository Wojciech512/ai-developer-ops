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
