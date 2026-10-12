# Notatki do sprawozdania

## Faza 0: setup
Środowisko: Python 3.13.12 w venv, selenium 4.51.0, pandas 3.0.6, matplotlib 3.11.2,
pytest 9.1.1, ruff 0.17.0 (`pip check` bez konfliktów). Utworzono szkielet pakietu
`bajtoparser/` (pages, parsing, utils, cli, pipeline) zgodny ze Strict Page Object Model.
Dwie żelazne zasady pilnowane są automatycznie hookami PreToolUse Claude Code (analiza AST):
zakaz `time.sleep` poza `utils/timing.py` i zakaz importu selenium w `main.py`, `cli.py`,
`pipeline.py`; hook odrzuca tylko zmiany dodające naruszenie. Weryfikacja: 12/12 przypadków
testowych hooków zgodnych z oczekiwaniem (7 odrzuconych, 5 przepuszczonych) oraz jedna
próba na żywo zablokowana.

## Faza 1: rekonesans
Rekonesans w Selenium (Chrome headless) wykazał, że tabela i karty to rozłączne zbiory
(30 wierszy + 42 karty = 72 rekordy na podstronę, 0 wspólnych `data-id`), więc parser musi
zbierać obie struktury. Marker panelu *Dostawa i zwroty* to `#panel-dostawa[data-wypelnione="tak"]`
(zdejmowane `hidden`), identyczny jak dla Specyfikacji. Doładowywanie: 6 porcji po 12
(`data-wczytano` 12 → 72, `data-porcji-lacznie` = 6); po ostatniej porcji przycisk
`#wczytaj-wiecej` zostaje w DOM, ma pusty tekst i jest niewidoczny, bez `disabled`.
Surowy HTML (`urllib.request`): `index.html` 3952 B i `produkt/P49235.html` 2770 B,
**0** rekordów (0 `tr.wiersz-produktu`, 0 `article.produkt`, 0 `data-id`), po 2 znaczniki
`<script>`; w DOM po skryptach 72 rekordy na podstronę. Wniosek: dane są wstrzykiwane
wyłącznie przez JavaScript. Pełna mapa selektorów: `docs/SELEKTORY.md`.

## Faza 2: czyszczenie danych
Funkcje czyszczące w `bajtoparser/parsing/` są czyste (bez selenium) i testowane bez
przeglądarki: 97 testów pytest, najpierw napisanych i uruchomionych bez implementacji
(`ModuleNotFoundError`), potem zielonych. Formaty surowych wartości ustalono z DOM-u
(podstrona 1 i 20 stron produktów), nie z założeń. Decyzje: (1) waluty nie są przeliczane,
cena to `float` + kod `PLN`/`EUR`/`USD`; (2) waluta wykrywana po symbolu (`zł`, `€`, `$`),
a znaczenie przecinka zależy od waluty: dla USD to separator tysięcy (`$1,299.00`), dla
PLN/EUR dziesiętny (`1 299,00 zł`); (3) prefiks `<span class="etykieta">` z kart usuwa
warstwa `pages/`, nie `parsing/`; (4) `gratis` w koszcie dostawy to `0.0` bez waluty;
(5) nieznana jednostka (np. waga w gramach) i niepoprawna data dają `None`, nie wyjątek;
(6) deduplikacja po `id` zachowuje pierwsze wystąpienie i zwraca liczbę usuniętych.

## Faza 3: infrastruktura
Całe czekanie na sztywno jest w `utils/timing.py` i przechodzi przez podmienialną funkcję,
więc testy retry i pauz nie czekają naprawdę; dekorator `@ponawiaj` łapie tylko trzy wyjątki
Selenium (backoff 1, 2, 4 s, 4 próby) i stoi wyłącznie na metodach najwyższego poziomu, żeby
próby się nie mnożyły, a diagnostyka (.png + .html) zapisywała się raz. `BasePage.tekst()` łapie
tylko `NoSuchElementException`, bo `TimeoutException` nie może udawać braku danych, a
`otworz()` robi pauzę grzecznościową 0,5 s przed każdym żądaniem poza pierwszym w sesji.
Testy: 135 pytest (bez Chrome'a). Weryfikacja w Chrome: `data-wczytano=12` po otwarciu `/`
w obu trybach, `pl-PL`, okno 1366x900; celowo nieistniejący selektor dał 4 próby,
opóźnienia 1/2/4 s, 3 retry i jedną parę plików diagnostycznych; przebieg z tą operacją trwał
19,66 s (okno) i 18,43 s (headless), więc różnicy trybów nie da się jeszcze ocenić.

## Faza 4: CatalogPage
**Zbieranie rekordów:** wybrano jedno `execute_script` zamiast klasycznego `find_element`
dla każdego pola. Wariant klasyczny to ok. 900 wywołań WebDrivera na podstronę (72 rekordy x 13
pól, ok. 5400 na przebieg) i ryzyko `StaleElementReferenceException` przy przerysowaniu DOM-u w
trakcie czytania; wariant ze skryptem to 1 wywołanie i atomowa migawka. Kosztem jest mniej
czytelny JS w stringu, więc skrypt jest statyczny, a selektory przekazuje Python (`arguments[0]`
ze stałych klasy), co zachowuje zasadę „selektory na górze klasy”. Strona nadal zwraca surowe
stringi; jedyna ingerencja to wycięcie `span.etykieta` z kart.
**Doładowywanie:** pętla czeka na WZROST `data-wczytano` (nie na migoczące `data-wczytywanie`),
kończy się przy `data-porcja == data-porcji-lacznie`, ma twardy limit 20 iteracji, a ponawianie
jest per porcja (`@ponawiaj` na `wczytaj_porcje`, pętla bez dekoratora). Liczbę podstron
(6) ustala `liczba_podstron()` z linków `a[href*="strona-"]`, nie stała.
**Liczby (podstrony 1 i 2, headless):** po 72 rekordy (30 tabela + 42 karta), 72 unikalne `id`,
`data-porcja` 6/6, 0 retry; czas otwarcia, doładowania 5 porcji i zebrania rekordów 9,93 s
(podstrona 1) i 13,43 s (podstrona 2). Braki w surowych danych na podstronie 1 / 2:
`cena_poprzednia` pusta w tabeli 19 / 26 i nieobecna w kartach 35 / 34 (brak promocji, nie brak
danych), `producent` `—` 17 / 14, `ocena` `—` 16 / 12. Odchylenie od README: `gwarancja` też
bywa `—` (6 na każdej z tych podstron); `czysc_gwarancje("—")` daje `None`, więc to nie wymaga zmian.

## Faza 5: ProductPage
**Atrybuty dostępne dopiero po interakcji (utrudnienie 5.0):** na 20 produktach z podstrony 1
panele *Specyfikacja* i *Dostawa i zwroty* mają przed kliknięciem 0 wypełnionych pól (20/20
produktów), a po kliknięciu zakładki i `data-wypelnione="tak"` odpowiednio 7 i 5 (20/20). Czyli
12 z 13 atrybutów szczegółów nie istnieje w DOM bez kliknięcia; 13. (opis) jest widoczny od razu.
**Decyzje:** zakładki otwierane osobno z własnym `@ponawiaj` (nie zagnieżdżone), pola czytane
jednym `execute_script` po otwarciu obu paneli (atomowa migawka, selektory z Pythona, `textContent`
zamiast `.text`, bo ukryty panel zwraca `''`). Strona produktu niczego nie połyka: nieistniejący
produkt (404 bez `data-stan-renderu`) kończy się `TimeoutException` po 4 próbach, diagnostyką
i wyjątkiem dla pipeline'u. Nagłówek `#karta-produktu` nie wnosi nowych atrybutów: to duplikaty
8 pól z listy plus nazwa i identyfikator, więc rekord ma 13 kluczy szczegółów.
**Liczby (20 produktów, co 3. rekord podstrony 1, headless):** 20/20 udanych, 0 retry,
średnio 0,66 s na produkt (otwarcie, 2 zakładki, odczyt; w tym pauza grzecznościowa 0,5 s),
13/13 pól niepustych w każdym z 20 produktów (na tej próbce brak `—` w polach szczegółów),
nazwa i kategoria z nagłówka zgodne z listą w 5/5 produktów.


## Faza 6: pipeline, CLI, eksport
**Polityka błędów w pipeline:** Page Objecty niczego nie połykają; pipeline łapie tylko wyjątki,
które zostają po wyczerpaniu retry (`WYJATKI_PONAWIANE`), liczy je jako błędy i idzie dalej.
Błąd produktu zostawia rekord z samymi danymi z listy (szczegóły `None`); błąd w trakcie
doładowywania podstrony pomija ją w całości (bez częściowych rekordów, numer w logu); błąd
otwarcia podstrony 1 jest krytyczny (bez niej nie wiadomo, ile jest podstron). Deduplikacja
po `id` jest PRZED wejściem w szczegóły, więc duplikaty nie generują żądań. Kody wyjścia:
0 sukces, 1 błędy częściowe lub Ctrl+C, 2 błąd krytyczny (np. serwis nie odpowiada: sprawdzenie
jednym żądaniem `urllib`, Chrome się nie uruchamia).
**Kontrola „nierozpoznanych”:** wartość, która nie była brakiem (`—`, pusta), a po czyszczeniu
wyszła `None`, jest liczona i logowana (jeden WARNING na rekord z listą pól). Dzięki temu błąd
parsera (nieznany format) nie udaje braku danych. Zapis w locie: każdy rekord (surowy + szczegóły)
trafia od razu do `<wyjscie>_surowe.jsonl`; CSV i JSON zapisują się na końcu, także po Ctrl+C.
**Format wyjścia:** 30 kolumn w stałej kolejności (`parsing/rekord.py: KOLUMNY`): 26 atrybutów
serwisu, z czego cena rozbita na `cena` + `waluta`, wymiary na `dlugosc_cm`/`szerokosc_cm`/
`wysokosc_cm`, koszt dostawy na `koszt_dostawy` + `waluta_dostawy` (gratis = 0.0 PLN), plus
`zrodlo` (tabela/karta). Liczby całkowite jako `Int64` (bez 25 -> 25.0), `ean` jako tekst.
**Liczby (headless):** `--strony 1 --limit 5`: 5 rekordów, 30 kolumn, 0 błędów, 14,19 s.
`--strony 2`: 144 pozycje na liście -> 143 po deduplikacji (1 duplikat, 0 różnych od oryginału),
143/143 ze szczegółami, 0 błędów, 0 retry, 0 nierozpoznanych, 113,88 s (ok. 0,64 s na produkt).
Waluty: 124 PLN / 11 EUR / 8 USD; źródło: 60 tabela / 83 karta; dostawa gratis: 39. Braki
(wszystkie to `—` w surowych danych): producent 31, ocena 27, gwarancja 12, waga 9;
`cena_poprzednia` pusta w 113 (brak promocji). Testy: 219 pytest (84 nowe), bez Chrome'a.
Kod wyjścia 2 przy niedostępnym serwisie jest pokryty testem jednostkowym (podmieniony
`serwis_odpowiada`, zamknięty port 127.0.0.1:1); próba z faktycznie zatrzymanym serwerem
na porcie 8000 do wykonania na początku fazy 7.
