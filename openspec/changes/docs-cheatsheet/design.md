# Design

## Context

Zobacz `proposal.md` — Why. Stan obecny: `README.md` ma 33 linie i sekcje `## Stos`, `## Instalacja raz na komputer`, `## Inicjalizacja projektu`, `## Proces` (jeden akapit prozy), `## Pliki`. Źródłem prawdy dla treści ściągawki są `skills/ops-feature/SKILL.md`, `skills/ops-review/SKILL.md`, `skills/ops-ship/SKILL.md`, `skills/ops-critique/SKILL.md`, `templates/agents/docs-researcher.md`, `AGENTS.md` oraz `scripts/install.sh` (symlinki `skills/*` do `~/.agents/skills/` dla Codex, stąd forma `$ops-*`). `make check` nie waliduje Markdown — zakres sprawdzeń to `*.sh`, `*.json`, `*.toml` i `tests/`.

## Goals / Non-Goals

**Goals:**
- Jedna tabela decyzyjna trzymająca się dosłownie nazw komend, które naprawdę istnieją w tym repo albo w zależnościach instalowanych przez `scripts/install.sh`.
- Sekcja mieści się w 40 liniach źródła, licząc nagłówek, tabelę i dwa akapity.
- Tabela renderuje się poprawnie na GitHub (GFM), potwierdzone rendererem GitHuba, nie podglądem edytora.

**Non-Goals:**
- Nie dublujemy sekcji `## Proces` ani `## Stos` — ściągawka jest warstwą "co wpisać", nie drugim opisem procesu.
- Nie dokumentujemy komend, których użytkownik nie ma po `scripts/install.sh`. Wyjątek dla zależności, które ten skrypt instaluje (`superpowers`, `openspec`/`opsx`, plugin security, plugin `codex`) — ich komendy są prawidłowym wejściem użytkownika i wchodzą do kolumny 2. Komendy wewnętrzne, których użytkownik nie wywołuje sam (`/opsx:propose`, `/opsx:verify`, `/code-review`), występują wyłącznie w kolumnie 3 jako opis tego, co dzieje się pod spodem.
- Żadnej automatyzacji sprawdzania Markdown w `Makefile` (to byłoby zmianą w skryptach, czyli non-goal z proposala).
- Nie dopisujemy pełnych reguł pierwszeństwa między sytuacjami. Tabela jest ściągawką, nie drzewem decyzyjnym; jedyne wzmocnienie to klauzula o obowiązkowym teście regresyjnym w akapicie (a).

## Treść do wstawienia (dosłownie)

To jest kompletna, zatwierdzona treść sekcji. Zadanie 2.1 i 2.2 wstawia dokładnie ten blok do `README.md`, bez przeredagowywania. Zmiana któregokolwiek identyfikatora wymaga ponownej weryfikacji z zadania 1.

```markdown
## Ściągawka według sytuacji

| Sytuacja | Wypisujesz | Co się dzieje pod spodem |
|---|---|---|
| Zmiana większa niż jedno zdanie | `/ai-developer-ops:ops-feature <id> "<cel>"` | OpenSpec propose -> `ops-critique` -> `using-git-worktrees` + `subagent-driven-development` + TDD -> `ops-review` -> `ops-ship` |
| Bug | `/superpowers:systematic-debugging`, potem `/ai-developer-ops:ops-review <zakres fiksa>` | test odtwarzający -> przyczyna -> fix; cztery etapy review. `HEAD~1..HEAD` dopiero gdy cały fix siedzi w ostatnim commicie |
| Review czegokolwiek (PR, MR, gałąź, ścieżka) | `/ai-developer-ops:ops-review <cel>` | `/code-review`, security, drugi model |
| Poprawka na jedno zdanie | zwykła prośba | hooki i `make check` pilnują; TDD z `AGENTS.md` odpala się samo |
| PR/MR | `/ai-developer-ops:ops-ship <id>` | warunki wstępne, szablon, dowody, boty |
| Pytanie o API biblioteki | `use docs-researcher: ...` | Context7 w subagencie |

**Czego nie mieszać.** Jeden plan i tylko jeden: `openspec/changes/<id>/tasks.md` — `superpowers:brainstorming` i `superpowers:writing-plans` odpalaj wyłącznie ręcznie, żeby nie powstał drugi plan, a zmianę prowadzoną przez OpenSpec zamykaj przez `ops-ship`, nie przez `superpowers:finishing-a-development-branch`. Bug zostaje bugiem nawet gdy fix ma jedną linię: test odtwarzający jest obowiązkowy.

**W Codex nie ma Superpowers.** Proces niosą skille `ops-*` z agentami TOML (`worker`, `reviewer`, `tester`, `explorer`, `docs_researcher`), wywołania to `$ops-feature`, `$ops-review`, `$ops-ship`; nie ma `systematic-debugging`, a agent od dokumentacji nazywa się `docs_researcher` z podkreśleniem.
```

Bilans linii: 1 nagłówek + 1 pusta + 2 wiersze szkieletu tabeli + 6 wierszy danych + 1 pusta + akapit + 1 pusta + akapit = 14 linii. Budżet 40 ma 26 linii zapasu.

Identyfikatory i ich źródła (zadanie 1 potwierdza każdy osobno):

| identyfikator | źródło potwierdzające |
|---|---|
| `ops-feature`, `ops-review`, `ops-ship`, `ops-critique` | `name:` we frontmatterze `skills/<nazwa>/SKILL.md` |
| prefiks `/ai-developer-ops:` | `name` w `.claude-plugin/plugin.json` + `skills/` w korzeniu pluginu |
| forma `$ops-*` | `scripts/install.sh`: `link_file "${s%/}" ~/.agents/skills/...` dla `skills/*/` |
| `superpowers:systematic-debugging`, `:brainstorming`, `:writing-plans`, `:using-git-worktrees`, `:subagent-driven-development`, `:finishing-a-development-branch` | `install_or_update_plugin superpowers superpowers-marketplace` w `scripts/install.sh` + lista skilli w działającej sesji |
| `docs-researcher` | `name:` w `templates/agents/docs-researcher.md` |
| `docs_researcher`, `worker`, `reviewer`, `tester`, `explorer` | nazwy plików w `codex/agents/*.toml` |
| `HEAD~1..HEAD` jako cel | reguła normalizacji `A..B` w `skills/ops-review/SKILL.md` |
| `make check` jako bramka | cel `check:` w `Makefile` + `scripts/stop-gate.sh` |

## Decisions

**1. Każda komenda w tabeli w backtickach.** Sprawdzone empirycznie rendererem GitHuba: `| /x <id> | ok |` renderuje się jako `<td>/x </td>` — GFM zjada `<id>` jako nieznany tag HTML. W backtickach to samo daje `<td><code>/x &lt;id&gt;</code></td>`. Backticki chronią `<id>`, `<cel>`, `<target>`. Alternatywa (encje `&lt;id&gt;`) odpadła: nieczytelna w źródle i niespójna z resztą README.

**2. Sekcja ląduje bezpośrednio po `## Proces`, przed `## Pliki`.** `## Proces` mówi "jak to działa", ściągawka "co wpisać" — naturalna kolejność. Alternatywa (na początku, przed `## Stos`) odpadła: czytelnik bez zainstalowanego pluginu nie ma jeszcze kontekstu dla nazw komend.

**3. Kolumna 3 to sekwencja oddzielona `->`, nie lista zagnieżdżona.** GFM nie wspiera list blokowych w komórkach tabeli bez `<br>`. `->` jest już konwencją w tym README (linia `## Proces`) i w `AGENTS.md`. Alternatywa (`<br>` + numeracja) odpadła: dłuższe źródło, ten sam efekt.

**4. Render weryfikuje renderer GitHuba, nie heurystyka na źródle.** `gh api --method POST /markdown -f mode=gfm -f "text=$(cat README.md)"` zwraca HTML od GitHuba. Asercje: w wyjściu istnieje `<table>` z trzema `<th>` i sześcioma `<tr>` w `<tbody>`, a placeholdery są widoczne jako `&lt;id&gt;`, `&lt;cel&gt;`, `&lt;target&gt;`. To wyłapuje też tryby awarii, których liczenie `|` nie widzi — na przykład niezamknięty blok kodu wcześniej w pliku, po którym cała tabela staje się tekstem. Liczenie `|` zostaje jako tani pre-check, ale nie jest dowodem. Nie twierdzimy, że którykolwiek check wyłapuje "wszystkie" awarie. Alternatywa (`markdownlint` w `make check`) odpadła: nowa zależność npm i zmiana w `Makefile` — oba poza zakresem. Alternatywa (ręczny podgląd na GitHub po pushu) odpadła: niepowtarzalna i spóźniona względem bramki.

**5. Treść sekcji jest zamrożona w tym pliku, w bloku "Treść do wstawienia (dosłownie)".** Wcześniejsza wersja tej decyzji odwoływała się do treści podanej w rozmowie, czego implementer w świeżym kontekście nie widzi — stąd BLOCKER z `critique.md`. Blok powyżej jest jedynym źródłem treści. Jedna korekta faktograficzna wobec pierwotnego brzmienia użytkownika w wierszu 4: "TDD odpala się samo" jest prawdziwe w Claude (auto-wywołanie `superpowers:test-driven-development`), ale w Codex Superpowers nie ma i regułę niesie `AGENTS.md`; komórka mówi więc "TDD z `AGENTS.md` odpala się samo", co jest prawdziwe w obu wariantach.

**6. Zakres zmiany mierzymy diffem wobec zapisanej bazy, nie `git status --porcelain`.** Workspace ma nieśledzone pliki niezwiązane ze zmianą (`.idea/misc.xml` istniał przed startem, `.tmp/` powstał na potrzeby `ops-critique` i nie jest w `.gitignore`), więc "`git status` wymienia tylko README.md" jest niespełnialne. Baza to `git rev-parse HEAD` zapisany przed edycją; sprawdzamy `git diff --name-only <baza>` dla śledzonych plików i osobno listę nieśledzonych z jawną listą dozwolonych. `.tmp/` usuwamy przed końcem.

## Risks / Trade-offs

- **Ściągawka rozejdzie się ze skillami po ich edycji** → zadanie 1 weryfikuje każdy identyfikator osobno wobec pliku źródłowego, ale to sprawdzenie jednorazowe. Ryzyko rozjazdu pozostaje po tej zmianie: repo nie ma mechanizmu wiążącego README ze `skills/` (konwencja "`templates/` to źródło prawdy" z `AGENTS.md` dotyczy kopiowanych plików, nie synchronizacji dokumentacji ze skillami). Świadomie przyjęte; zamknięcie wymagałoby testu w `tests/`, czyli zmiany w skryptach — non-goal.
- **Brak trafienia przy weryfikacji identyfikatora** → zadanie 1 zatrzymuje się i raportuje użytkownikowi. Nie usuwamy po cichu wiersza, bo wiersz niesie wymaganą informację; rozbieżność nazwy jest sygnałem o repo, nie o tabeli.
- **40 linii źródła nie gwarantuje czytelności** → długi wiersz tabeli liczy się jako jedna linia, a kolumna 3 w wierszu 1 jest długa. Budżet mierzy objętość sekcji, nie szerokość; nie obiecujemy "bez przewijania". Jeśli budżet pęknie, skraca się kolumnę 3, nie usuwa wiersza.
- **Polska wersja README vs angielskie nazwy komend** → komendy zostają dosłowne (są identyfikatorami), proza polska, zgodnie z resztą pliku.
