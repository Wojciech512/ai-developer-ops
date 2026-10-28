# Spec Delta

## Purpose

Rekonesans repozytorium i utrzymanie jednego wizualnego artefaktu architektury, który agent czyta przed planowaniem: deterministycznie renderowany diagram sekwencji komponentów wraz z legendą wskazującą istniejące pliki, odświeżany mechanicznie po każdej zmianie i pilnowany bramką zgodności obrazu ze źródłem.

## ADDED Requirements

### Requirement: Rekonesans w równoległych subagentach read-only

Skill SHALL prowadzić rekonesans w subagentach read-only, po jednym na obszar. Obszary to: punkty wejścia, komponenty i ich odpowiedzialności, przepływ danych, integracje zewnętrzne, zadania w tle. W Claude Code subagentem jest `Explore`, w Codex `explorer`.

#### Scenario: Pięć obszarów w jednym przebiegu

- **WHEN** użytkownik uruchamia `ops-discover` bez flag
- **THEN** skill zleca pięć zadań rekonesansu, jedno na obszar, równolegle w jednej turze
- **AND** każde zadanie wykonuje subagent bez prawa zapisu

#### Scenario: Harness ogranicza równoległość

- **WHEN** harness nie pozwala uruchomić pięciu subagentów naraz
- **THEN** skill dzieli zadania na wsady
- **AND** każdy z pięciu obszarów jest pokryty dokładnie raz

#### Scenario: Subagent obszaru zawodzi dwa razy

- **WHEN** subagent jednego obszaru zawodzi, zostaje ponowiony raz i zawodzi ponownie
- **THEN** przebieg zatrzymuje się i raport nazywa obszar, który padł
- **AND** model nie jest zapisany ani zmodyfikowany

#### Scenario: Subagent nie modyfikuje analizowanego projektu

- **WHEN** rekonesans kończy się
- **THEN** żaden plik analizowanego projektu poza `docs/` nie jest zmieniony

### Requirement: Model architektury jest jedynym wejściem renderera

Skill SHALL zapisywać wynik rekonesansu do `docs/architecture.model.json`: listę komponentów (identyfikator, etykieta, warstwa, ścieżka) oraz listę interakcji (źródło, cel, czasownik, nazwa operacji, przepływ, numer porządkowy). Renderer SHALL czytać wyłącznie ten model i SHALL NOT analizować kodu projektu.

#### Scenario: Renderowanie nie zależy od treści kodu

- **WHEN** renderer działa na drzewie, w którym każda ścieżka z modelu istnieje, ale wszystkie pliki są puste
- **THEN** `docs/architecture.puml` powstaje z treścią identyczną jak w repozytorium źródłowym

#### Scenario: Model odwołuje się do nieistniejącego komponentu

- **WHEN** interakcja wskazuje `from` albo `to`, którego nie ma w `components`
- **THEN** renderer kończy się kodem różnym od zera i nazywa ten identyfikator

#### Scenario: Model narusza schemat

- **WHEN** model ma nieznane pole, `layer` spoza słownika, zduplikowane `components[].id`, zduplikowane `flows[].id`, `interactions[].flow` bez odpowiadającego przepływu, `seq` niebędące liczbą całkowitą, zero przepływów `main` albo więcej niż jeden przepływ `main`
- **THEN** renderer kończy się kodem różnym od zera i nazywa naruszoną regułę
- **AND** wypisuje wszystkie naruszenia tego modelu, nie tylko pierwsze

### Requirement: Renderer jest czystą funkcją modelu

Renderer SHALL produkować bajtowo identyczny `docs/architecture.puml` dla modelu o identycznej treści, niezależnie od kolejności wpisów w modelu i od czasu uruchomienia. Uczestnicy i grupy SHALL być ułożeni w stałym porządku: najpierw według warstwy, potem alfabetycznie według identyfikatora. `.puml` SHALL NOT zawierać daty, znacznika czasu ani innej wartości zmiennej w czasie.

#### Scenario: Przetasowana kolejność w modelu

- **WHEN** renderer dostaje dwa modele różniące się wyłącznie kolejnością wpisów w `components`, `flows` i `interactions`
- **THEN** oba wyjścia `.puml` są bajtowo identyczne

#### Scenario: Dwa różne czasy uruchomienia

- **WHEN** ten sam model jest renderowany dwa razy przy różnych wartościach zegara systemowego
- **THEN** oba wyjścia `.puml` są bajtowo identyczne

### Requirement: Reguły nazewnicze stabilizują wynik rekonesansu

Skill SHALL wymuszać na modelu reguły, które czynią dwa przebiegi rekonesansu zbieżnymi: zamknięty słownik warstw, identyfikator wyprowadzony z nazwy komponentu, numer porządkowy nadawany krokiem dziesięć, zakaz klasy i funkcji jako komponentu, zakaz ścieżki nieistniejącej w repozytorium. Zgodność dwóch kolejnych przebiegów SHALL być potwierdzona jednorazowo i zapisana jako dowód; nie jest ona gwarantowana przez bramkę automatyczną.

#### Scenario: Identyfikator poza konwencją

- **WHEN** model ma `components[].id` niezgodne z wzorcem `^[A-Z][A-Za-z0-9]*$` albo kończące się na `Group`
- **THEN** renderer kończy się kodem różnym od zera i nazywa ten identyfikator

#### Scenario: Dowód zbieżności dwóch przebiegów

- **WHEN** `ops-discover` jest uruchomiony dwa razy pod rząd bez zmian w kodzie
- **THEN** różnica między `.puml` z obu przebiegów jest zapisana jako dowód
- **AND** różnica niepusta zatrzymuje zadanie i jest raportowana użytkownikowi

### Requirement: Uczestnikami diagramu są komponenty, nie klasy ani funkcje

Diagram SHALL mieć jako uczestników komponenty aplikacji: API, serwisy, repozytoria, bazę, kolejkę, cache, integracje zewnętrzne, UI. Klasa ani funkcja SHALL NOT być uczestnikiem. Warstwy SHALL być grupowane konstrukcją `box`.

#### Scenario: Warstwa jako box

- **WHEN** model ma komponenty w co najmniej dwóch warstwach
- **THEN** każdy uczestnik `.puml` leży w `box` swojej warstwy
- **AND** kolejność boxów jest stała między uruchomieniami

### Requirement: Limit dwunastu uczestników z agregacją nadmiaru

Diagram SHALL mieć nie więcej niż dwunastu uczestników. Gdy rekonesans znajdzie więcej komponentów, nadmiar SHALL być zagregowany w uczestnika zbiorczego w obrębie swojej warstwy, a legenda SHALL wymieniać ścieżki wszystkich komponentów wchodzących w agregat.

#### Scenario: Czternaście komponentów w modelu

- **WHEN** model opisuje czternaście komponentów
- **THEN** `.puml` deklaruje nie więcej niż dwunastu uczestników
- **AND** co najmniej jeden uczestnik jest agregatem
- **AND** legenda w `docs/ARCHITECTURE.md` pokrywa wszystkie czternaście ścieżek

#### Scenario: Dwunaście komponentów w modelu

- **WHEN** model opisuje dwunastu komponentów
- **THEN** żaden uczestnik nie jest agregatem

#### Scenario: Operacja powtórzona w przebiegu po agregacji

- **WHEN** przebieg wykonuje tę samą operację dwukrotnie, rozdzieloną inną wiadomością, a oba jej końce wpadają do jednego agregatu
- **THEN** oba wystąpienia zostają w `.puml`

### Requirement: Każda strzałka ma czasownik i nazwę operacji

Każda wiadomość w `.puml` wygenerowana z modelu SHALL mieć etykietę złożoną z czasownika i nazwy operacji. Interakcja z pustym czasownikiem lub pustą nazwą operacji SHALL powodować błąd renderera.

#### Scenario: Interakcja bez czasownika

- **WHEN** interakcja w modelu ma puste pole czasownika albo pole złożone wyłącznie z białych znaków
- **THEN** renderer kończy się kodem różnym od zera i wskazuje tę interakcję

### Requirement: Znaki łamiące format są odrzucane

Renderer SHALL odrzucić model, w którym tytuł, etykieta, czasownik albo nazwa operacji zawiera znak mogący złamać składnię PlantUML lub Markdown, w szczególności cudzysłów, backtick, znak nowej linii, kreskę pionową albo nawias trójkątny. Ścieżka SHALL dopuszczać spację, lecz SHALL NOT dopuszczać backticka ani znaku nowej linii.

#### Scenario: Cudzysłów w nazwie operacji

- **WHEN** nazwa operacji zawiera cudzysłów
- **THEN** renderer kończy się kodem różnym od zera, nazywa pole i wypisuje niedozwolony znak

#### Scenario: Ścieżka ze spacją

- **WHEN** komponent ma ścieżkę zawierającą spację, a plik o tej ścieżce istnieje
- **THEN** render kończy się powodzeniem
- **AND** wpis w legendzie pozostaje jednym wierszem

### Requirement: Jeden diagram obejmuje przebieg główny i przebiegi niezależne

Repozytorium SHALL mieć dokładnie jeden diagram. `.puml` SHALL zawierać przebieg główny od wejścia użytkownika do odpowiedzi, a przebiegi niezależne — zadania w tle i webhooki — SHALL być w tym samym diagramie jako `group` z nazwą przebiegu.

#### Scenario: Job w tle obok przebiegu głównego

- **WHEN** rekonesans znajduje zadanie w tle
- **THEN** `.puml` ma `group` z nazwą tego przebiegu
- **AND** nie powstaje drugi plik `.puml` ani drugi obraz

### Requirement: docs/ARCHITECTURE.md ma dokładnie cztery części

`docs/ARCHITECTURE.md` SHALL zawierać dokładnie: tytuł, osadzony obraz `docs/architecture.svg`, sekcję `## Legenda uczestników`, sekcję `## Ostatnia aktualizacja` z datą, zakresem i skrótem commita. Żadnej innej sekcji tekstowej SHALL NOT być.

#### Scenario: Brak dodatkowych sekcji

- **WHEN** `docs/ARCHITECTURE.md` jest wygenerowany
- **THEN** plik ma dokładnie dwa nagłówki `##`: `Legenda uczestników` i `Ostatnia aktualizacja`
- **AND** ma dokładnie jeden nagłówek `#` i dokładnie jedno osadzenie obrazu

#### Scenario: Data i commit poza diagramem

- **WHEN** `docs/ARCHITECTURE.md` i `docs/architecture.puml` są wygenerowane z tego samego modelu
- **THEN** data i skrót commita występują w `docs/ARCHITECTURE.md`
- **AND** nie występują w `docs/architecture.puml`

### Requirement: Legenda pokrywa każdego uczestnika istniejącą ścieżką

Legenda SHALL mieć jedną linię na uczestnika diagramu po agregacji. Każdy uczestnik SHALL mieć wpis. Wpis uczestnika zbiorczego SHALL wymieniać ścieżki wszystkich zagregowanych komponentów. Każda wymieniona ścieżka SHALL istnieć w repozytorium, z wyjątkiem uczestnika warstwy `actor`, który SHALL mieć wpis bez ścieżki.

#### Scenario: Ścieżka wskazuje nieistniejący plik

- **WHEN** model podaje dla komponentu ścieżkę, której nie ma w repozytorium
- **THEN** renderer kończy się kodem różnym od zera i wypisuje tę ścieżkę

#### Scenario: Uczestnik bez wpisu w legendzie

- **WHEN** `.puml` deklaruje uczestnika, dla którego legenda nie ma linii
- **THEN** renderer kończy się kodem różnym od zera

#### Scenario: Aktor bez ścieżki

- **WHEN** komponent warstwy `actor` ma ścieżkę `null`
- **THEN** render kończy się powodzeniem
- **AND** jego wpis w legendzie nie zawiera ścieżki

#### Scenario: Komponent spoza warstwy actor bez ścieżki

- **WHEN** komponent warstwy innej niż `actor` ma ścieżkę `null`
- **THEN** renderer kończy się kodem różnym od zera

### Requirement: Dokumenty powstają razem albo wcale

Renderer SHALL zakończyć całą walidację i wygenerować treść obu dokumentów przed zapisaniem któregokolwiek z nich. Przy jakimkolwiek błędzie walidacji SHALL NOT zmienić `docs/architecture.puml` ani `docs/ARCHITECTURE.md`. Zapis każdego pliku SHALL być atomowy.

#### Scenario: Niepoprawny model przy istniejących dokumentach

- **WHEN** render jest uruchomiony na niepoprawnym modelu w katalogu z istniejącymi `architecture.puml` i `ARCHITECTURE.md`
- **THEN** kod wyjścia jest różny od zera
- **AND** treść obu istniejących plików pozostaje niezmieniona

### Requirement: Odświeżanie zachowuje ręczne dopiski

Z flagą `--refresh` skill SHALL porównać odkryte komponenty i interakcje z istniejącym `.puml`, dodać nowe, usunąć nieistniejące i zachować linie oznaczone komentarzem `' manual`. Linia oznaczona `' manual` SHALL NOT nigdy zostać usunięta.

#### Scenario: Komponent usunięty z kodu

- **WHEN** komponent obecny w `.puml` nie istnieje już w kodzie i `ops-discover --refresh` zostaje uruchomiony
- **THEN** uczestnik i jego interakcje znikają z `.puml`
- **AND** jego linia znika z legendy

#### Scenario: Ręczny dopisek przetrwał odświeżenie

- **WHEN** `.puml` ma linię z komentarzem `' manual` w sekcji, która nadal istnieje, i `ops-discover --refresh` zostaje uruchomiony
- **THEN** ta linia jest obecna w nowym `.puml` w niezmienionej treści
- **AND** leży w tej samej sekcji co wcześniej

#### Scenario: Powtórne odświeżenie bez zmian w modelu

- **WHEN** odświeżenie jest uruchomione dwa razy na niezmienionym modelu, za każdym razem zachowując dopiski z poprzedniego wyjścia
- **THEN** drugie wyjście jest bajtowo identyczne z pierwszym

### Requirement: Ręczny dopisek ma zamkniętą składnię

Ręczny dopisek SHALL być jedną linią będącą wiadomością, notą albo pełnoliniowym komentarzem. Dopisek SHALL NOT deklarować uczestnika, boxa, grupy ani sterować aktywacją. Dopisek niespełniający tych warunków SHALL powodować błąd renderera nazywający linię i dopuszczalne formy.

#### Scenario: Dopisek deklaruje uczestnika

- **WHEN** `.puml` zawiera linię `participant X ' manual`
- **THEN** renderer kończy się kodem różnym od zera, cytuje tę linię i wypisuje dopuszczalne formy dopisku

#### Scenario: Dopisek nie podlega walidacji etykiety

- **WHEN** ręczny dopisek jest wiadomością, której etykieta nie zawiera czasownika
- **THEN** render kończy się powodzeniem

### Requirement: Dopisek bez swojej sekcji trafia do sierot jako komentarz

Dopisek, którego sekcja już nie istnieje, albo który odwołuje się do uczestnika nieobecnego po agregacji, SHALL być zachowany przed `@enduml` jako linia zakomentowana, oznaczona jako sierota, w stałej kolejności. Taki dopisek SHALL NOT pozostać linią wykonywalną.

#### Scenario: Grupa dopisku przestała istnieć

- **WHEN** przepływ zawierający ręczny dopisek znika z modelu i odświeżenie zostaje uruchomione
- **THEN** treść dopisku jest obecna w nowym `.puml` jako linia zakomentowana w bloku sierot
- **AND** liczba uczestników deklarowanych w `.puml` nie rośnie

#### Scenario: Raport wymienia przeniesione dopiski

- **WHEN** odświeżenie przenosi dopisek do bloku sierot
- **THEN** raport skilla wymienia ten dopisek

### Requirement: Flaga scope ogranicza rekonesans i uzgadnia model po własności

Z flagą `--scope <ścieżki>` rekonesans SHALL objąć tylko podane ścieżki. Komponent SHALL należeć do zakresu, gdy jego ścieżka leży w jednej z podanych ścieżek lub pod nią; interakcja SHALL należeć do zakresu swojego źródła. Wpisy poza zakresem SHALL zostać bez zmian.

#### Scenario: Odświeżenie zawężone do plików zmiany

- **WHEN** `ops-discover --refresh --scope src/api` jest uruchomiony
- **THEN** subagenty czytają tylko `src/api`
- **AND** komponenty spoza `src/api` zachowują dotychczasowe wpisy w modelu

#### Scenario: Interakcja wisi po usunięciu komponentu

- **WHEN** komponent w zakresie znika, a interakcja spoza zakresu nadal go wskazuje
- **THEN** ta interakcja jest usunięta z modelu
- **AND** raport skilla ją wymienia

#### Scenario: Zakres opróżniłby przebieg główny

- **WHEN** uzgodnienie pozostawiłoby przebieg `main` bez żadnej interakcji
- **THEN** odświeżenie kończy się błędem wskazującym za wąski zakres
- **AND** model pozostaje niezmieniony

#### Scenario: Zawężony rekonesans bez istniejącego modelu

- **WHEN** `--scope` jest użyty w repozytorium bez `docs/architecture.model.json`
- **THEN** powstaje model obejmujący wyłącznie podany zakres
- **AND** raport mówi wprost, że wynik nie jest pełną architekturą

### Requirement: Zakres odświeżenia po zmianie jest zapisywany przed scaleniem

Zakres odświeżenia po zmianie SHALL być wyznaczony i zapisany przed scaleniem gałęzi, z uwzględnieniem plików usuniętych. Krok po scaleniu SHALL czytać ten zapis i SHALL NOT wyliczać zakresu z historii po scaleniu. Brak zapisu albo zapis pusty SHALL skutkować pominięciem odświeżenia z jawnym komunikatem.

#### Scenario: Zakres zawiera plik usunięty w zmianie

- **WHEN** zmiana usuwa plik komponentu
- **THEN** zapisany zakres zawiera ścieżkę tego pliku

#### Scenario: Zapis zakresu nie istnieje

- **WHEN** krok po scaleniu nie znajduje zapisanego zakresu
- **THEN** odświeżenie jest pominięte z komunikatem
- **AND** nie uruchamia się rekonesans całego repozytorium

### Requirement: Dokument onboardingowy na żądanie

Z flagą `--onboarding` skill SHALL dodatkowo wygenerować `docs/ONBOARDING.md`: uruchomienie lokalne, kolejność czytania plików, do pięciu ścieżek wykonania krok po kroku z odwołaniem do uczestników diagramu i co najmniej jedną taką ścieżkę, oraz od pięciu do dziesięciu pytań z odpowiedziami i odwołaniami do plików. Dokument SHALL mieć nie więcej niż dwieście linii źródła. Bez tej flagi plik SHALL NOT powstać.

#### Scenario: Uruchomienie bez flagi

- **WHEN** `ops-discover` jest uruchomiony bez `--onboarding`
- **THEN** `docs/ONBOARDING.md` nie powstaje ani nie jest modyfikowany

#### Scenario: Ścieżki wykonania odwołują się do diagramu

- **WHEN** `docs/ONBOARDING.md` jest wygenerowany
- **THEN** każda ścieżka wykonania nazywa uczestników obecnych w legendzie `docs/ARCHITECTURE.md`
- **AND** każde pytanie ma odpowiedź z odwołaniem do istniejącego pliku
- **AND** plik ma nie więcej niż dwieście linii

#### Scenario: Repozytorium ma mniej niż pięć przebiegów

- **WHEN** repozytorium ma trzy rozpoznane przebiegi wykonania
- **THEN** dokument opisuje trzy ścieżki
- **AND** raport podaje, ile przebiegów repozytorium faktycznie ma

### Requirement: Render diagramu rozróżnia brak narzędzia od nieudanego renderu

Cel `make docs` SHALL generować `docs/architecture.svg` z `docs/architecture.puml`, używając lokalnego `plantuml`, a gdy go nie ma, obrazu `plantuml/plantuml` w Dockerze. Brak obu narzędzi SHALL kończyć się ostrzeżeniem i kodem zero. Obecne narzędzie, które zawiodło, SHALL kończyć się kodem różnym od zera.

#### Scenario: Brak plantuml i brak Dockera

- **WHEN** `make docs` jest uruchomiony bez lokalnego `plantuml` i bez Dockera
- **THEN** cel wypisuje ostrzeżenie z nazwą brakującego narzędzia i kończy się kodem zero
- **AND** nie przerywa innych celów

#### Scenario: Narzędzie obecne, render nieudany

- **WHEN** `make docs` jest uruchomiony, a render zawodzi z powodu niedostępnego demona Dockera albo niepoprawnego `.puml`
- **THEN** cel kończy się kodem różnym od zera i przekazuje komunikat narzędzia
- **AND** zapis wiążący obraz ze źródłem nie jest aktualizowany

### Requirement: Bramka wiąże obraz ze źródłem po treści

Cel `make check` SHALL kończyć się błędem, gdy `docs/architecture.svg` nie został wygenerowany z aktualnej treści `docs/architecture.puml`. Zgodność SHALL być stwierdzana po sumie kontrolnej treści źródła, SHALL NOT po czasie modyfikacji plików. Gdy `docs/architecture.puml` nie istnieje, sprawdzenie SHALL przejść bez efektu.

#### Scenario: Źródło zmienione bez ponownego renderu

- **WHEN** `.puml` jest zmieniony bez ponownego renderu i `make check` zostaje uruchomiony
- **THEN** `make check` kończy się kodem różnym od zera i nazywa nieodświeżony plik

#### Scenario: Świeży klon repozytorium

- **WHEN** repozytorium jest sklonowane, przez co czasy modyfikacji wszystkich plików są czasem klonowania, a zacommitowany SVG pochodzi z innej treści `.puml`
- **THEN** `make check` kończy się kodem różnym od zera

#### Scenario: Render i źródło zgodne

- **WHEN** `make docs` zakończył się powodzeniem i `.puml` nie był potem zmieniany
- **THEN** sprawdzenie przechodzi

#### Scenario: Repozytorium bez diagramu

- **WHEN** `make check` jest uruchomiony w repozytorium bez `docs/architecture.puml`
- **THEN** sprawdzenie przechodzi i nie zgłasza błędu

### Requirement: Skill działa w repozytorium bez skryptów narzędzia

Skill SHALL rozwiązywać ścieżkę renderera względem katalogu instalacji narzędzia, nie względem analizowanego repozytorium. Skill SHALL działać w repozytorium, które nie zawiera żadnych plików z `scripts/` tego narzędzia.

#### Scenario: Uruchomienie w świeżym repozytorium projektu

- **WHEN** `ops-discover` jest uruchomiony w repozytorium bez katalogu `scripts/` narzędzia
- **THEN** renderer jest uruchomiony z katalogu instalacji narzędzia
- **AND** dokumenty architektury powstają w `docs/` analizowanego repozytorium

### Requirement: Rekonesans jest wywoływany przez init i po scaleniu zmiany

Skill `init` SHALL wywołać `ops-discover` w miejsce własnego kroku rekonesansu i SHALL pozyskać z jego raportu komendy uruchomienia, budowania, testów i lintu. Skill `ops-feature` SHALL po archiwizacji zmiany wywołać `ops-discover --refresh` z zapisanym zakresem tej zmiany.

#### Scenario: Inicjalizacja repozytorium

- **WHEN** `init` dochodzi do kroku rekonesansu
- **THEN** wywołuje `ops-discover` i nie zawiera własnego opisu rekonesansu
- **AND** komendy do wypełnienia celów `Makefile` pochodzą z raportu `ops-discover`

#### Scenario: Istniejący Makefile projektu nie dostał nowych celów

- **WHEN** `init` zachował istniejący `Makefile` zamiast skopiować szablon
- **THEN** raport dla człowieka wymienia cele renderu i bramki zgodności do dopisania ręcznie

#### Scenario: Zmiana zarchiwizowana

- **WHEN** `ops-feature` kończy archiwizację zmiany
- **THEN** wywołuje `ops-discover --refresh` z zakresem zapisanym przed scaleniem

### Requirement: Odświeżenie po scaleniu kończy się commitem

Odświeżenie po scaleniu zmiany SHALL zakończyć się commitem zmienionych dokumentów architektury. Krok SHALL NOT zostawić zmodyfikowanych dokumentów niezacommitowanych.

#### Scenario: Odświeżenie zmieniło dokumenty

- **WHEN** odświeżenie po scaleniu zmienia `docs/architecture.puml` i `docs/ARCHITECTURE.md`
- **THEN** powstaje commit zawierający te pliki i odświeżony obraz
- **AND** drzewo robocze jest czyste

#### Scenario: Gałąź domyślna jest chroniona

- **WHEN** odświeżenie po scaleniu nie może commitować na gałąź domyślną
- **THEN** powstaje osobna gałąź i propozycja scalenia z szablonu projektu

### Requirement: AGENTS.md kieruje agenta do diagramu i wskazuje właściciela aktualizacji

Szablon `AGENTS.md` SHALL zawierać instrukcję: przed planowaniem przeczytaj `docs/ARCHITECTURE.md`; nieaktualność zgłoś w raporcie; nie poprawiaj diagramu w trakcie zadania. Instrukcja SHALL wskazywać `ops-discover` jako jedyny sposób aktualizacji diagramu.

#### Scenario: Agent napotyka nieaktualny diagram

- **WHEN** agent w trakcie zadania widzi, że diagram nie zgadza się z kodem
- **THEN** zgłasza to w raporcie
- **AND** nie zmienia `docs/architecture.puml` ani `docs/ARCHITECTURE.md` w ramach tego zadania

#### Scenario: Zakaz nie blokuje odświeżenia przez narzędzie

- **WHEN** agent wykonuje krok odświeżenia architektury przez `ops-discover`
- **THEN** zakaz poprawiania diagramu w trakcie zadania go nie dotyczy
