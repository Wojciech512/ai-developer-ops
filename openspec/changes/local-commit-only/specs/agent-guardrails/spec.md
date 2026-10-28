# Spec Delta

## Purpose

Określa, czego agentowi nie wolno zrobić w repozytorium, i wymusza to mechanicznie, a nie tylko opisem w dokumentacji. Pierwszym obszarem jest zapis przenoszący kod na zdalne repozytorium. Bramka jest barierą przed domyślną ścieżką, nie sandboxem przed celowym obejściem.

## ADDED Requirements

### Requirement: Agent nie wykonuje operacji przenoszącej kod na zdalne
Agent MUST NOT wykonać bezpośredniego wywołania operacji, która przenosi kod lub tworzy wydanie na zdalnym repozytorium: wypchnięcia commitów, utworzenia lub zmergowania PR/MR, utworzenia release'u lub tagu na zdalnym. Blokada MUST działać niezależnie od nazwy zdalnego i od tego, czy podano URL zamiast nazwy. Zablokowana próba MUST zakończyć się komunikatem mówiącym, że pracę agenta kończy commit lokalny, a komendę uruchamia człowiek.

#### Scenario: Wypchnięcie na gałąź zdalną
- **WHEN** agent próbuje wykonać `git push origin HEAD:main`
- **THEN** operacja jest zablokowana przed nawiązaniem połączenia ze zdalnym
- **AND** komunikat błędu mówi, co agent ma zrobić zamiast tego

#### Scenario: Zdalny podany jako URL albo pod inną nazwą
- **WHEN** agent próbuje wykonać `git push https://github.com/x/y.git HEAD:main` albo `git push upstream main`
- **THEN** operacja jest zablokowana — zakaz nie jest zawężony do zdalnego o nazwie `origin`

#### Scenario: Operacja za separatorem powłoki lub z przekierowaniem katalogu
- **WHEN** agent próbuje wykonać `make check && git push`, `git status; git push` albo `git -C /inna/sciezka push`
- **THEN** operacja jest zablokowana — dopasowanie nie opiera się wyłącznie na prefiksie komendy

#### Scenario: Utworzenie lub zmergowanie PR/MR oraz release
- **WHEN** agent próbuje wykonać `gh pr create`, `gh pr merge`, `gh release create`, `glab mr create` albo `glab mr merge`
- **THEN** operacja jest zablokowana

#### Scenario: Zapis przez API hostingu
- **WHEN** agent próbuje wykonać `gh api` z metodą zapisującą, na przykład `gh api --method POST /repos/o/r/git/refs`
- **THEN** operacja jest zablokowana

### Requirement: Praca lokalna, odczyt zdalnego i komentarze pozostają dozwolone
Bramka MUST NOT blokować pracy, która nie przenosi kodu na zdalne. Commit lokalny, bramki jakości, odczyt ze zdalnego oraz komentowanie istniejącego PR/MR MUST przechodzić. Tekst opisujący zabronioną komendę MUST być traktowany jako dane, nie jako jej wywołanie, żeby bramka nie blokowała przygotowania materiałów dla człowieka.

#### Scenario: Commit lokalny i bramka jakości
- **WHEN** agent wykonuje `git commit` albo `make check`
- **THEN** operacja przechodzi, bo commit lokalny jest oczekiwanym wynikiem pracy agenta

#### Scenario: Odczyt zdalnego i API niezapisujące
- **WHEN** agent wykonuje `gh pr view`, `gh pr list`, `git fetch` albo `gh api --method POST /markdown`
- **THEN** operacja przechodzi
- **AND** `gh api --method POST /markdown` pozostaje dostępne, bo służy jako dowód poprawnego renderowania Markdown

#### Scenario: Komentarz na istniejącym PR/MR
- **WHEN** agent publikuje komentarz z wynikiem review na PR/MR otwartym przez człowieka
- **THEN** operacja przechodzi, bo komentarz nie przenosi kodu

#### Scenario: Zabroniona komenda jako tekst w argumencie
- **WHEN** agent wykonuje `git commit -m "Dokumentuje git push"` albo zapisuje do pliku instrukcję zawierającą `git push -u origin <branch>`
- **THEN** operacja przechodzi, bo zabroniony ciąg występuje jako dane, nie jako wywoływana operacja

### Requirement: Bramka chroni własną konfigurację
Pliki definiujące bramkę — jej skrypt, rejestrację hooków i wpisy uprawnień — MUST być chronione przed edycją przez agenta na tych samych zasadach, co pozostałe ścieżki chronione. Bez tego bramkę można wyłączyć jedną edycją, co czyniłoby ją pozorną.

#### Scenario: Próba edycji skryptu bramki
- **WHEN** agent próbuje zmodyfikować skrypt bramki, plik rejestracji hooków albo plik uprawnień
- **THEN** edycja jest zablokowana z komunikatem, że zmiana wymaga zgody człowieka

### Requirement: Niemożność oceny komendy skutkuje odmową
Jeśli bramka nie jest w stanie ocenić komendy, MUST odmówić, a nie przepuścić — ale tylko wtedy, gdy komenda w ogóle wygląda na operację zapisu na zdalne. Brak zależności, nieparsowalne wejście i nieoczekiwany kształt wejścia MUST być traktowane jako niemożność oceny.

#### Scenario: Brak zależności do parsowania przy komendzie ryzykownej
- **WHEN** narzędzie do parsowania wejścia jest niedostępne, a surowe wejście zawiera ciąg wskazujący na operację zapisu na zdalne
- **THEN** operacja jest zablokowana z komunikatem o niemożności oceny komendy

#### Scenario: Brak zależności do parsowania przy komendzie zwykłej
- **WHEN** narzędzie do parsowania wejścia jest niedostępne, a surowe wejście nie zawiera żadnego ciągu wskazującego na operację zapisu na zdalne
- **THEN** operacja przechodzi, żeby brak zależności nie zablokował całej pracy lokalnej

#### Scenario: Wejście nieparsowalne lub o nieoczekiwanym kształcie
- **WHEN** wejście nie jest poprawnym JSON-em, pole komendy ma wartość puste, `null` albo typ inny niż tekst
- **THEN** bramka zachowuje się zgodnie z tą samą zasadą: blokuje, gdy surowe wejście wygląda na operację zapisu na zdalne, w przeciwnym razie przepuszcza

### Requirement: Zakaz jest udokumentowany dla wariantu bez hooków
Projekt MUST nieść zakaz również w instrukcjach czytanych natywnie przez agenta, który nie korzysta z mechanizmu hooków. Dla takiego wariantu egzekwowanie jest instrukcyjne, nie mechaniczne, i spec MUST NOT twierdzić inaczej.

#### Scenario: Wariant bez wsparcia hooków
- **WHEN** agent działa w narzędziu, w którym hooki nie obowiązują
- **THEN** zakaz jest obecny w instrukcjach projektu czytanych przez to narzędzie
- **AND** obejmuje dowolne zdalne, nie tylko `origin`, oraz PR/MR i release'y

#### Scenario: Nowy projekt po inicjalizacji
- **WHEN** użytkownik inicjalizuje nowy projekt procesem ai-developer-ops
- **THEN** nowy projekt dostaje zakaz w instrukcjach i w uprawnieniach, bez ręcznego dopisywania

### Requirement: Skill wydania przygotowuje wydanie, ale go nie wykonuje
Skill odpowiedzialny za wydanie zmiany MUST NOT sam pushować ani otwierać PR/MR. MUST sprawdzić warunki wstępne, przygotować commit oraz wypełnioną treść PR/MR w pliku w katalogu zmiany, a następnie podać człowiekowi komendy do uruchomienia. Definicja ukończenia pracy agenta MUST kończyć się na tym, co agent może zrobić sam.

#### Scenario: Warunki wstępne spełnione
- **WHEN** człowiek uruchamia skill wydania dla zmiany z zieloną bramką i review bez BLOCKER-a
- **THEN** skill przygotowuje treść PR/MR w pliku w katalogu zmiany
- **AND** nie wykonuje żadnej operacji przenoszącej kod na zdalne
- **AND** wypisuje komendy, które człowiek ma uruchomić

#### Scenario: Niespełnione warunki wstępne
- **WHEN** człowiek uruchamia skill wydania, a bramka nie jest zielona albo review ma nierozwiązany BLOCKER
- **THEN** skill zatrzymuje się i raportuje, czego brakuje, bez przygotowywania wydania

#### Scenario: Ponowne uruchomienie przy istniejącej treści PR/MR
- **WHEN** człowiek uruchamia skill wydania, a plik z treścią PR/MR już istnieje z poprzedniego przebiegu
- **THEN** skill nadpisuje go aktualną treścią i mówi, że to zrobił, zamiast kończyć się błędem
