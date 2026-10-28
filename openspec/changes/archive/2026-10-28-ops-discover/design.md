# Design

## Context

Zobacz `proposal.md` — Why. Stan obecny: rekonesans żyje w jednym zdaniu `skills/init/SKILL.md:9` i produkuje prozę. `docs/ARCHITECTURE.md` (82 linie) powstał raz. `Makefile` ma cele `check`, `lint`, `typecheck`, `test`, `fmt-file`, `e2e`; `typecheck` obejmuje `*.sh` (`bash -n`), `*.json` (`jq`), `*.toml` (`tomllib`) — Pythona produkcyjnego jeszcze nie ma. `scripts/` to wyłącznie bash zgodny z 3.2 (bez `mapfile`, bez tablic asocjacyjnych). `plantuml` 1.2026.8 jest zainstalowany lokalnie, Docker też. `scripts/install.sh:95` symlinkuje `skills/*/` do `~/.agents/skills/`, więc nowy katalog skilla rejestruje się sam. `scripts/init.sh` kopiuje szablony przez `cp_if_absent`, czyli nigdy nie nadpisuje plików użytkownika.

Trzy decyzje zapadły przed projektowaniem: (1) to repo dogfooduje skill — `docs/ARCHITECTURE.md` zostaje zastąpiony formą wizualną; (2) `SKILL.md` po angielsku, dokumenty generowane po polsku; (3) determinizm `.puml` zapewnia skrypt renderujący z modelu JSON.

Trzy kolejne zapadły po `ops-critique` (`critique.md`): (4) świeżość SVG pilnuje suma kontrolna, nie czas modyfikacji; (5) wymaganie determinizmu jest rozdzielone na renderer (SHALL, testowalne) i rekonesans (reguły nazewnicze + jednorazowy dowód); (6) limit uczestników jest górną granicą, nie wartością dokładną.

## Goals / Non-Goals

**Goals:**

- Determinizm `.puml` wynika z konstrukcji: renderer jest czystą funkcją modelu, a każda decyzja o kolejności i agregacji należy do renderera, nie do rekonesansu.
- Model ma możliwie mało stopni swobody, bo każdy z nich jest miejscem, w którym dwa przebiegi rekonesansu mogą się rozjechać.
- Renderer zawodzi głośno i odrzuca, nie escapuje. Niespójny model kończy się błędem i nie dotyka plików wyjściowych.
- Każda obietnica w specu ma mechanizm, który ją sprawdza, albo jest zapisana jako jednorazowy dowód w `evidence.md`. Żadnego SHALL bez weryfikacji.
- Integracja z `init` nie gubi tego, po co `init` robił rekonesans: komend build/test/lint/run do wypełnienia TODO.

**Non-Goals:**

- Nie dotykamy `README.md`. Wiersz ściągawki należy do zmiany `docs-cheatsheet`, która jest w toku (`0/13 tasks`) i edytuje ten sam fragment.
- Renderer nie czyta kodu projektu i nie wnioskuje architektury. Analiza jest zadaniem subagentów; renderer waliduje i formatuje.
- Nie śledzimy tożsamości komponentu przez zmianę nazwy. Rename w zakresie to usunięcie plus dodanie (decyzja 13).
- Nie automatyzujemy wykrywania rozjazdu model-kod. `make check` pilnuje wyłącznie zgodności SVG z `.puml`.
- Nie dodajemy drugiego diagramu, widoku komponentów ani diagramu per przepływ.

## Model architektury (schemat)

`docs/architecture.model.json`. Jedyne wejście renderera i jedyny artefakt, który pisze rekonesans.

```json
{
  "title": "ai-developer-ops",
  "components": [
    { "id": "Developer", "label": "developer", "layer": "actor", "path": null },
    { "id": "Installer", "label": "install.sh", "layer": "api", "path": "scripts/install.sh" }
  ],
  "flows": [
    { "id": "main", "label": "Instalacja i inicjalizacja", "kind": "main" },
    { "id": "prepush", "label": "Bramka pre-push", "kind": "independent" }
  ],
  "interactions": [
    { "flow": "main", "from": "Developer", "to": "Installer", "verb": "uruchamia", "op": "install.sh", "seq": 10 }
  ]
}
```

Pełny schemat. Każda reguła jest wymuszana przez `validate` i każda ma test (zadania 1.2–1.4).

| pole | typ | reguła |
|---|---|---|
| `title` | string | niepusty, reguły znaków jak `label` |
| `components` | array | niepusta |
| `components[].id` | string | `^[A-Z][A-Za-z0-9]*$`, unikalne, nie kończy się na `Group` (zarezerwowane dla agregatów, decyzja 3) |
| `components[].label` | string | niepusty, reguły znaków niżej |
| `components[].layer` | string | dokładnie jedna z: `actor`, `ui`, `api`, `service`, `repository`, `data`, `integration` |
| `components[].path` | string albo `null` | `null` dozwolone tylko dla `layer: "actor"`; w pozostałych warstwach wymagane i musi istnieć pod `--root` |
| `flows` | array | niepusta, dokładnie jeden wpis `kind: "main"` |
| `flows[].id` | string | `^[a-z][a-z0-9-]*$`, unikalne |
| `flows[].label` | string | niepusty, reguły znaków niżej |
| `flows[].kind` | string | `main` albo `independent` |
| `interactions` | array | niepusta |
| `interactions[].flow` | string | musi wskazywać istniejące `flows[].id` |
| `interactions[].from`, `.to` | string | muszą wskazywać istniejące `components[].id` |
| `interactions[].verb`, `.op` | string | niepuste po przycięciu białych znaków, reguły znaków niżej |
| `interactions[].seq` | integer | liczba całkowita; `float`, string i `bool` odrzucone |

Nieznane pole na każdym poziomie jest odrzucane — inaczej literówka w nazwie pola przechodziłaby po cichu.

**Reguły znaków: odrzucamy, nie escapujemy.** `title`, `label`, `verb`, `op` dopuszczają litery (w tym diakrytyki), cyfry, spację i `- _ . / ( ) : ,`. Wszystko inne — w szczególności `"`, backtick, `|`, `\`, `<`, `>`, znak nowej linii — jest błędem walidacji nazywającym pole i znak. `path` dopuszcza dodatkowo spację, ale nie backtick ani nowej linii. Odrzucanie wybrano nad escapowaniem, bo te wartości są krótkie i pisane przez agenta: reguła „popraw model" jest jednoznaczna, a escapowanie musiałoby być poprawne jednocześnie dla PlantUML i dla Markdown, co jest dwoma różnymi zestawami znaków specjalnych i cichym źródłem rozjazdu.

## Decisions

**1. Renderer w Pythonie, `typecheck` zyskuje krok dla `*.py` tylko w tym repo.** Zadanie renderera to parsowanie JSON, sortowanie wielokluczowe, grupowanie i generowanie tekstu. W bashu 3.2 bez tablic asocjacyjnych wymagałoby to `jq` z nietrywialnymi wyrażeniami plus klejenia w shellu — trudniejszego do przetestowania niż sam problem. `python3` jest już twardą zależnością (`Makefile` rozwiązuje `PY`, `tests/` to `unittest`). Koszt: `scripts/render_arch.py` byłby pierwszym plikiem produkcyjnym bez bramki, więc `typecheck` dostaje `$(PY) -m py_compile` po `git ls-files '*.py'`. **Ten krok wchodzi wyłącznie do `Makefile` w korzeniu, nie do `templates/Makefile`** — gatuje nasz renderer, który nie jest dostarczany do projektów docelowych, a w cudzym repo z tysiącem plików `.py` byłby nieproszonym kosztem. Jest to świadomy wyjątek od konwencji „`templates/` to źródło prawdy" z `AGENTS.md` i dlatego jest tu zapisany. Alternatywa (bash + jq) odpadła na testowalności; alternatywa (Python bez bramki) łamie „`make check` zielone" jako definicję done.

**2. Determinizm rozdzielony: renderer gwarantowany, rekonesans ustabilizowany regułami.** Renderer jest czystą funkcją modelu i to jest SHALL udowodniony testem (ten sam model przetasowany daje bajtowo to samo wyjście). Stabilność rekonesansu nie jest gwarantowana przez nic, co umiemy uruchomić w `make check`, więc nie jest zapisana jako SHALL na całym potoku — to byłoby wymaganie bez weryfikacji. Zamiast tego SHALL-em są reguły, które ją wymuszają: zamknięty słownik warstw, `id` wyprowadzone z nazwy komponentu, `seq` krokiem 10, zakaz klas i funkcji jako uczestników, zakaz `path` nieistniejącej. Zgodność dwóch przebiegów pod rząd jest jednorazowym dowodem w `evidence.md` (zadanie 8.3). `.puml` nie zawiera daty ani commita — te trafiają wyłącznie do `## Ostatnia aktualizacja` w `ARCHITECTURE.md`, więc `.puml` nie zmienia się z upływem czasu.

**3. Agregacja należy do renderera; limit 12 jest górną granicą.** Reguła: dopóki liczba uczestników przekracza 12, wybierz warstwę o największej liczbie niezagregowanych komponentów (remis rozstrzyga późniejsza pozycja w słowniku warstw — nadmiarem są zwykle integracje), zwiń całą tę warstwę w jednego uczestnika o `id` `<Layer>Group` i etykiecie `"<nazwa warstwy> (n)"`. Zwinięcie całej warstwy przeskakuje poniżej 12 (14 komponentów w układzie 4/4/3/3 daje 11), dlatego spec mówi „nie więcej niż dwunastu", nie „dokładnie dwunastu" — `critique.md` pokazał, że poprzednie brzmienie było nieosiągalne dla własnej fikstury. Sufiks `Group` jest zarezerwowany w walidacji `id`, żeby wygenerowany agregat nie mógł kolidować z komponentem z modelu.

Przepisanie interakcji przy zwijaniu:

- Interakcje do i z komponentów zwiniętych wskazują agregat.
- Interakcja, której oba końce wpadły do tego samego agregatu, staje się wiadomością do siebie (`X -> X`) — nie jest usuwana, bo jej zniknięcie zmieniłoby liczbę kroków przebiegu.
- Deduplikacja jest **wyłącznie sąsiedzka**: po posortowaniu scalane są jedynie wiadomości identyczne i stojące obok siebie. Globalna deduplikacja po (`flow`, `from`, `to`, `verb`, `op`) gubiła drugie wystąpienie operacji wykonywanej w przebiegu dwukrotnie — to był WARN z `critique.md`. Powtórzenie rozdzielone inną wiadomością zostaje.

**4. Kolejność wyjścia.** Uczestnicy sortują się po (indeks warstwy w słowniku, `id`); boxy idą w kolejności słownika warstw. Przepływy: `main` pierwszy, potem `independent` alfabetycznie po `id`; każdy `independent` ląduje w `group` z etykietą przepływu. Wiadomości w przepływie po (`seq`, `from`, `to`, `verb`, `op`) — klucze po `seq` są tie-breakerem, żeby dwie wiadomości o tym samym `seq` nie zależały od kolejności w pliku. Diagram sekwencji nie może sortować wiadomości alfabetycznie, bo kolejność jest jego treścią; stąd jawne `seq`.

**5. Ręczne dopiski: zamknięta składnia, kotwice sekcji, sieroty zakomentowane.** `--refresh` renderuje z modelu, więc dopisek przepadłby bez osobnego mechanizmu. `critique.md` pokazał, że poprzedni projekt pozwalał dopiskiem obejść każdą inną gwarancję. Stąd trzy ograniczenia:

- **Dopuszczalna składnia**: wiadomość (`A -> B : tekst`, `A --> B : tekst`), nota (`note left of X : tekst`, `note right of X : tekst`) albo pełnoliniowy komentarz. Zawsze jedna linia. Dopisek zaczynający się od `participant`, `actor`, `box`, `end box`, `group`, `end`, `activate`, `deactivate`, `@startuml`, `@enduml` jest błędem walidacji nazywającym linię i wypisującym dopuszczalne formy. Dzięki temu dopisek nie może zadeklarować uczestnika, czyli nie może przekroczyć limitu 12 ani ominąć legendy. Dopisek-wiadomość jest zwolniony z walidacji „czasownik plus operacja", bo jego treść jest wolnym tekstem.
- **Kotwice**: renderer emituje po otwarciu boxa linię `' layer:<layer>`, a po otwarciu grupy `' flow:<id>`. `--preserve` przypisuje dopisek do sekcji po kotwicy, nie po etykiecie. Etykiety nie są unikalne i mogą się zmienić; `layer` i `flow.id` są unikalne z walidacji.
- **Sieroty**: dopisek z sekcji, która już nie istnieje, albo odwołujący się do uczestnika, którego nie ma po agregacji, wraca jako **linia zakomentowana** `' manual (orphan) <oryginalna treść>` przed `@enduml`, posortowana. Komentarz jest istotny: żywa wiadomość do nieistniejącego uczestnika kazałaby PlantUML utworzyć go automatycznie, co przekroczyłoby limit uczestników i ominęło legendę. Treść jest zachowana, wykonanie wyłączone.

Dopiski wracają na koniec swojej sekcji, posortowane po pełnej treści linii — sortowanie czyni powrót deterministycznym niezależnie od pozycji dopisku wcześniej. Linia z `' manual` nigdy nie jest usuwana.

**6. Walidacja przed zapisem; podkomenda `all` dla spójności dwóch plików.** `critique.md` słusznie zauważył, że dwie osobne podkomendy nie mogą zagwarantować, iż nie powstanie nowy `.puml` przy starym `ARCHITECTURE.md`. Dlatego `all` waliduje raz, renderuje oba dokumenty **w pamięci**, a dopiero potem zapisuje każdy przez plik tymczasowy w katalogu docelowym i `os.replace`. Gwarancja jest zawężona uczciwie: po walidacji i renderowaniu pozostaje okno dwóch wywołań `rename`, nie okno renderowania — awaria uprawnień, braku miejsca czy błąd gita zdarzą się przed pierwszym zapisem, nie między zapisami. `puml` i `md` zostają do częściowego przerenderowania i każda z nich zapisuje swój plik atomowo. Przy jakimkolwiek błędzie walidacji kod wyjścia to 1, wszystkie błędy lecą na stderr naraz, a żaden plik nie jest dotknięty.

**7. Interfejs: cztery podkomendy.** `validate --model M [--root R] [--preserve P]`; `puml --model M --out O [--preserve P] [--root R]`; `md --model M --out O --scope S [--date D] [--commit C] [--root R]`; `all --model M --puml-out O1 --md-out O2 --scope S [--preserve P] [--date D] [--commit C] [--root R]`. `--root` domyślnie `.` i wyznacza katalog, wobec którego sprawdzane jest istnienie `path`. `--date` domyślnie dzisiejsza data UTC, `--commit` domyślnie `git rev-parse --short HEAD`; obie flagi istnieją, żeby test mógł podstawić stałe i żeby `ARCHITECTURE.md` był odtwarzalny.

**8. Świeżość pilnuje suma kontrolna, nie czas modyfikacji.** `make docs` po udanym renderze zapisuje `docs/architecture.svg.sha256` — surowy skrót `.puml`, z którego SVG powstał. `docs-fresh` liczy skrót `.puml` i porównuje z zawartością pliku. Czas modyfikacji odrzucono: git nie przywraca `mtime`, więc po świeżym klonie przestarzały zacommitowany SVG przechodziłby bramkę, a równe znaczniki czasu (render w tej samej sekundzie) są nieodróżnialne od przestarzałości — `critique.md` nazwał to zinstytucjonalizowanym fałszywym negatywem i miał rację. Alternatywa (przerenderowanie i `diff`) odpadła: wymagałaby `plantuml` albo Dockera na każdej maszynie uruchamiającej `make check`, w tym w CI. Skrót liczy `shasum -a 256`, a gdy go nie ma — `sha256sum`; brak obu to błąd bramki, nie ciche przejście. Gdy `docs/architecture.puml` nie istnieje, bramka przechodzi bez efektu, żeby repo bez diagramu nie miało czerwonego `make check`.

**9. `make docs`: brak narzędzia ostrzega, obecne narzędzie musi się udać.** Kolejność prób: `plantuml -tsvg`, potem `docker run --rm -v "$PWD/docs:/data" plantuml/plantuml -tsvg /data/architecture.puml`. Rozróżnienie, którego brakowało w poprzedniej wersji: **narzędzia nie ma** (brak `plantuml` i brak `docker` na PATH) → ostrzeżenie z nazwą brakującego narzędzia i wyjście 0, zgodnie z „kroki opcjonalne warn-and-continue" z `AGENTS.md`. **Narzędzie jest, ale render zawiódł** (zatrzymany demon Dockera, nieudany pull obrazu, niepoprawny `.puml`) → kod wyjścia niezerowy i stderr narzędzia. W obu przypadkach `docs/architecture.svg.sha256` **nie jest** aktualizowany, więc stary SVG zostaje wykryty przez `docs-fresh` jako nieświeży, a nie wzięty za aktualny.

**10. `init` wywołuje `ops-discover --onboarding` i czyta z raportu komendy.** Krok 3 w `init` służył dwóm celom: `ARCHITECTURE.md` oraz komendom build/test/lint/run dla kroku 4. Model JSON tych komend nie niesie i nie powinien — to nie architektura. Dlatego `init` woła wariant `--onboarding`: „uruchomienie lokalne" jest sekcją `ONBOARDING.md`, a raport końcowy skilla (wyjście w rozmowie, nie plik) wymienia stos i wykryte komendy. Bez tego podstawienia `init` straciłby wejście do kroku 4.

**11. Zakres odświeżenia jest zapisywany przed merge'em, nie liczony po nim.** Poprzednia wersja liczyła `git diff --name-only $(git merge-base HEAD main)..HEAD` po merge'u. Sprawdzone empirycznie: po merge'u do `main` `merge-base HEAD main` to sam `HEAD`, więc diff jest pusty i krok 8 `ops-feature` byłby cichym no-opem. Dodatkowo filtrowanie do „katalogów istniejących po merge'u" wycinało usunięcia, czyli dokładnie to, czego odświeżenie potrzebuje, by usunąć nieistniejące komponenty. Nowa reguła: **`ops-ship` przed merge'em zapisuje `openspec/changes/<id>/scope.txt`** — wynik `git diff --name-only --diff-filter=ACMRD $(git merge-base HEAD origin/main)..HEAD`, jedna ścieżka na linię, z usunięciami (`D`) włącznie. Krok 8 czyta ten plik (po archiwizacji dostępny pod `openspec/changes/archive/<id>/scope.txt`) i nie liczy niczego sam. Pusty albo brakujący `scope.txt` oznacza pominięcie odświeżenia z jawnym komunikatem, nie odświeżenie całego repo.

**12. Odświeżenie po merge'u ma właściciela i commit.** Krok 8 `ops-feature` nie jest zakończony, dopóki drzewo nie jest czyste. Po `ops-discover --refresh --scope <lista>` uruchamia `make docs` i commituje `docs(architecture): refresh after <id>`. Gdy domyślna gałąź jest chroniona, powstaje mała gałąź `docs/refresh-<id>` i PR/MR z tego samego szablonu. `critique.md` słusznie wskazał, że poprzednia wersja zostawiała zmodyfikowane dokumenty bez właściciela — czyli brudny checkout i przestarzałe repo.

**13. Uzgadnianie przy `--scope`: własność po ścieżce, sieroty raportowane.** Bez jawnych reguł zawężony rekonesans mógł zostawić wiszące interakcje. Reguły:

- Komponent jest **w zakresie**, gdy jego `path` leży w którejś ze ścieżek `--scope` albo pod nią. Komponent `actor` (`path: null`) jest zawsze poza zakresem — aktora nie wyznacza plik.
- Komponenty w zakresie zastępuje wynik rekonesansu (dodane, zmienione, usunięte). Komponenty poza zakresem zostają bez zmian.
- Interakcja należy do zakresu swojego `from`. Interakcje z `from` w zakresie zastępuje rekonesans; pozostałe zostają.
- Interakcja wskazująca po uzgodnieniu komponent, którego już nie ma, jest **usuwana i wymieniana w raporcie skilla**. Zostawienie jej wywróciłoby walidację; ciche usunięcie ukryłoby zmianę architektury.
- Przepływ bez żadnej interakcji po uzgodnieniu jest usuwany. Gdyby usunięty miał być przepływ `main`, odświeżenie kończy się błędem „zakres za wąski" i nie zapisuje modelu.
- **Rename nie jest śledzony**: komponent o zmienionym `id` to usunięcie plus dodanie, a dopiski odwołujące się do starego `id` stają się sierotami (decyzja 5). Śledzenie tożsamości wymagałoby stabilnego klucza, którego rekonesans nie ma.
- `--scope` **bez istniejącego modelu**: dozwolone, powstaje model obejmujący tylko zakres, a raport mówi wprost, że to nie jest pełna architektura. `--refresh` bez istniejącego modelu jest równoważne pełnemu rekonesansowi.

**14. Skill rozwiązuje ścieżkę renderera jak `init`.** `render_arch.py` żyje w repo pluginu, nie w projekcie docelowym, a `init.sh` nie kopiuje `scripts/`. `SKILL.md` ustala więc `ROOT = $CLAUDE_PLUGIN_ROOT if set, otherwise ~/.ai-developer-ops` — identycznie jak `skills/init/SKILL.md:6` — i woła `"$ROOT/scripts/render_arch.py"`. Dla Codex działa ten sam fallback, bo `~/.ai-developer-ops` wskazuje repo pluginu, a `~/.agents/skills/ops-discover` jest tylko symlinkiem do katalogu skilla. Cele `docs` i `docs-fresh` w projekcie docelowym nie potrzebują skryptu — to czysty shell.

**15. Projekty już zainicjalizowane dostają cele ręcznie.** `cp_if_absent` nigdy nie nadpisuje `Makefile`, więc repo zainicjalizowane przed tą zmianą nigdy nie zobaczy `docs` ani `docs-fresh`. Krok 7 `init` (raport „co wymaga człowieka") wypisuje więc oba cele do wklejenia, gdy `Makefile` został zachowany, a nie utworzony. Automatyczne wstrzyknięcie celu do cudzego `Makefile` odpada: łamie idempotencję, która jest w `AGENTS.md` wymieniona jako konwencja.

**16. Rekonesans: pięć obszarów, wsadowanie dozwolone, awaria zatrzymuje.** Pięć zadań w jednej turze jest formą domyślną. Gdy harness ogranicza równoległość, wsadowanie jest dozwolone, pod warunkiem że każdy obszar jest pokryty dokładnie raz. Obszar, którego subagent zawiódł, jest ponawiany raz; drugie niepowodzenie zatrzymuje przebieg z informacją, który obszar padł. Model częściowy nie jest zapisywany — niepełny rekonesans wyglądałby jak architektura, z której coś zniknęło.

**17. Zakaz poprawiania diagramu w trakcie zadania nie dotyczy `ops-discover`.** Linia w `AGENTS.md` mówi „nie poprawiaj w trakcie zadania", a krok 8 `ops-feature` nakazuje automatyczne odświeżenie — bez jawnego wyjątku agent dostawał sprzeczne instrukcje (open question z `critique.md`). Linia kończy się więc zdaniem, że aktualizacją zajmuje się wyłącznie `ops-discover`, wołany w kroku 8 `ops-feature` albo ręcznie.

**18. SVG osadzony relatywną ścieżką.** `![Diagram sekwencji](architecture.svg)` — relatywnie wobec `docs/ARCHITECTURE.md`. Bezwzględna `docs/architecture.svg` byłaby zepsuta w widoku katalogu `docs/`.

**19. Budżet `ONBOARDING.md` jest mierzalny, liczba ścieżek elastyczna.** „Max 4 strony" nie jest sprawdzalne bez ustalenia renderowania, a „dokładnie 5 ścieżek" jest niewykonalne w repo, które ma mniej niż pięć przebiegów. Budżet to **200 linii źródła** (mierzone `grep -c '^'`, konwencja jak limit 40 linii dla sekcji README i 60 dla `AGENTS.md`), **do pięciu** ścieżek wykonania (co najmniej jedna) i **do dziesięciu** pytań (co najmniej pięć). Mniej ścieżek niż pięć wymaga zdania w raporcie, ile przebiegów repo faktycznie ma.

## Risks / Trade-offs

- **Stabilność rekonesansu zależy od modelu językowego** → decyzje 2–4 przenoszą do renderera wszystko, co da się przenieść; `SKILL.md` domyka resztę regułami nazewniczymi. Ryzyko pozostaje realne: dwa przebiegi mogą nazwać ten sam serwis inaczej. Po decyzji 2 spec tego nie obiecuje — gwarantuje determinizm renderera (test) i reguły (walidacja), a zgodność dwóch przebiegów jest jednorazowym dowodem w `evidence.md`. `make check` tego nie pilnuje i spec tego nie twierdzi.
- **Odrzucanie znaków zamiast escapowania odrzuci legalny model** → nazwa operacji z `"` albo ścieżka z backtickiem zatrzymają render, choć są poprawne w swoim języku. Przyjęte świadomie: komunikat mówi, które pole i który znak, a poprawka to jedno słowo w modelu. Escapowanie poprawne jednocześnie dla PlantUML i Markdown jest większym źródłem błędów niż ten koszt.
- **Zamknięty słownik warstw nie pasuje do każdego projektu** → siedem warstw pokrywa aplikację webową z jobami i integracjami. Projekt o innej topologii (CLI, biblioteka, monorepo) będzie upychał komponenty w najbliższą warstwę. Determinizm kolejności boxów jest wart tej sztywności; rozszerzenie słownika to jedna linia w rendererze i w `SKILL.md`.
- **To repo nie jest aplikacją webową** → mapowanie `install.sh` na `api`, hooków na `service`, `templates/` na `data` będzie naciągane. Dogfooding na nietypowym projekcie jest jednak mocniejszym testem niż na typowym.
- **12 uczestników to mało dla dużego monolitu** → zwinięcie całej warstwy zachowa czytelność, ale zgubi szczegół; legenda zostaje pełna, więc ścieżki nie przepadają. Gdy agregat zjada warstwę kluczową dla przebiegu głównego, właściwą reakcją jest `--scope`, nie podniesienie limitu.
- **Suma kontrolna wiąże SVG ze źródłem, nie z kodem** → `docs-fresh` dowodzi, że SVG powstał z tego `.puml`. Nie dowodzi, że `.puml` opisuje aktualny kod. Tego nie pilnuje żadna bramka i pilnować nie będzie; za to odpowiada `--refresh` z kroku 8 `ops-feature`.
- **Sierota jako komentarz jest cicha** → zakomentowany dopisek nie znika, ale i nie krzyczy. Mitygacja: raport skilla wymienia każdy dopisek przeniesiony do sierot, więc zmiana jest widoczna w momencie, w którym zachodzi, a nie dopiero przy czytaniu `.puml`.
- **`py_compile` to słaba bramka** → wyłapie błąd składni, nie błąd typu. Mocniejsza (mypy, ruff) to nowa zależność, czyli zmiana stosu wymagająca zgody użytkownika. `py_compile` plus testy jednostkowe renderera są tym, co mamy bez nowej zależności.
- **Zastąpienie `docs/ARCHITECTURE.md` usuwa opis, którego diagram nie odda** → proza zawiera pułapki i uzasadnienia („repo jest własnym marketplace'em", „dogfooduje własny proces"), których diagram sekwencji nie wyraża. Zostaje w historii gita, a nośnikiem takiej wiedzy jest `AGENTS.md` i `docs/adr/`. Strata realna i przyjęta zgodnie z decyzją użytkownika.
