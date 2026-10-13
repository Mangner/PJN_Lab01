# Audyt wymagań (faza 9)

Data audytu: 2026-10-13 (zaktualizowany po dodaniu `docs/LAB1.pdf`). Zakres:
`docs/LAB1.pdf`, `docs/WYMAGANIA.md`, reguły z `CLAUDE.md`, kod, testy, `output/`, `logs/`,
`analiza/wyniki/`. Audyt był tylko do odczytu (kod, testy, dane i
`../Web-App/` bez zmian). Uruchomiono: `pytest` (**240 passed**, 2,61 s), `ruff check .`
(All checks passed), `ruff format --check .` (56 files already formatted). Chrome nie był
uruchamiany; dowody z przebiegów pochodzą z istniejących logów i plików.

Statusy: **zrealizowany** / **częściowo** / **brak**.

## 0. Braki i słabe punkty

Stan po przeczytaniu `docs/LAB1.pdf` i rozstrzygnięciach autora. Żaden obowiązkowy punkt
(wobec `WYMAGANIA.md` ani wobec oryginału PDF) nie ma statusu „brak”.

### 0.1 Otwarte lub z zastrzeżeniem

| # | Punkt | Status | Opis | Decyzja / co dalej |
|---|---|---|---|---|
| 3 | **Kolejność wymiarów `dlugosc_cm` / `szerokosc_cm` / `wysokosc_cm`** | **otwarte** | `czysc_wymiary` przypisuje liczby z tekstu `a x b x c cm` kolejno do długości, szerokości i wysokości (`parsing/pola.py:54`). Serwis nie podpisuje osi. Rozkłady (lampy 36 x 191 x 47, telefony 7 x 14 x 1) sugerują inne znaczenie. Wartości przepisane poprawnie (0 niezgodnych z surowym tekstem), wątpliwa jest tylko nazwa kolumn. | Autor sprawdzi z kluczem odpowiedzi (jutro, 2026-10-14). Do tego czasu w sprawozdaniu „wymiar 1/2/3” albo [DO UZUPEŁNIENIA]. Bez zmian w kodzie. |
| 4 | **Spearman jako Pearson rang** | zostaje, z zastrzeżeniem | `analiza/statystyki.py:193-194`: `a.rank().corr(b.rank())`, bo `scipy` nie jest w `requirements.txt`. Wynik poprawny (rangi uśrednione przy remisach), ale bez p-wartości; istotność to przybliżony próg \|r\| ≈ 1,96/√(n−1). | Decyzja: bez zmian w kodzie, zastrzeżenie w sprawozdaniu (sekcja 5). |
| 5 | **Usunięte duplikaty nie są w żadnym pliku danych** | zostaje, z zastrzeżeniem | 12 duplikatów istnieje tylko jako liczba w logu (`logs/bajtoparser_20261013_001635.log`, „duplikatów=12 (różnych od oryginału: 0)”); `okno_surowe.jsonl` ma 420 linii. PDF wymaga tylko liczby duplikatów przed i po odrzuceniu, co jest spełnione (432 → 420). | Decyzja: bez zmian w kodzie, zastrzeżenie w sprawozdaniu (sekcja 4). |
| 9 | **Okno vs headless: pojedyncza para przebiegów** | zostaje, z zastrzeżeniem | okno 351,59 s, headless 410,30 s (różnica 58,71 s, ok. 17%). Brak powtórzeń; czas zależy od losowego opóźnienia porcji serwisu (0,3-2 s) i pauz 0,5 s. | Decyzja: bez powtórzeń, zastrzeżenie w sprawozdaniu (sekcja 6.2). |
| 7 | **Retry nie zadziałał w pełnych przebiegach** | informacja | Oba pełne przebiegi: `retry=0`, `błędów=0`. Zachowanie 1/2/4 s potwierdzają testy (`tests/test_retry.py`, `tests/test_timing.py`) i kontrolowana próba z fazy 3 (nieistniejący selektor: 4 próby, opóźnienia 1/2/4 s, 3 retry, jedna para plików diagnostycznych). W `diagnostyka/`: 4 pary `.png`+`.html` z 2026-10-11 (`BasePage_kliknij`). | Opisać w sprawozdaniu rzetelnie: retry zweryfikowany testami i jedną kontrolowaną próbą, nie błędem produkcyjnym. |
| 8 | **`logs/`, `output/`, `diagnostyka/`, `scratch/` w `.gitignore`** | informacja | Dowody liczbowe nie są w repozytorium; trafią do ZIP-a tylko po ręcznym dołączeniu. | Przy pakowaniu dołączyć `output/`, `logs/`, `analiza/`, `docs/`. |

### 0.2 Nowe obserwacje z porównania z PDF-em

| # | Obserwacja | Status | Opis |
|---|---|---|---|
| P1 | **Dokładnie 2 rozszerzenia z listy 5.0, zero zapasu** | informacja | PARSER 5.0 wymaga „co najmniej 2” rozszerzeń: mamy headless z pomiarem czasu i diagnostykę (`.png` + `.html`). Obsługa 429, checkpoint i porównanie pamięci są poza zakresem, JSON z `dane/` pominięty decyzją. Utrata któregokolwiek z dwóch zejdzie poniżej progu. |
| P2 | **PDF nie mówi wprost „wszystko z 4.0” dla PARSERA 5.0** | informacja | To zdanie jest w PDF-ie tylko dla AUTORA 5.0. Przyjęto interpretację kumulatywną (jak `WYMAGANIA.md`: 4.0 + 5.0); spełnione też bez niej, więc ryzyko zerowe. |
| P3 | **Sprawozdanie wymaga opisu serwisu (rola AUTOR)** | do ustalenia | PDF wymienia „opis zbudowanego serwisu” jako element sprawozdania. Szkic go pomija (decyzja: należy do kolegi). Sprawozdanie w jednym PDF-ie na parę musi go zawierać od partnera. |
| P4 | **Sprawozdanie ma być PDF** | do zrobienia | Jest szkic `docs/SPRAWOZDANIE.md`, brak PDF-a. |
| P5 | **`WYMAGANIA.md` pomija trzy drobne punkty 3.0 z PDF-a** | spełnione | „minimum 60 wierszy” (mamy 420), „CSV lub XLSX” (mamy CSV i JSON), „opóźnienie między żądaniami” bez liczby (mamy ≥ 0,5 s). Bez konsekwencji. |
| P6 | **Rozszerzenie 4.0 „walidacja typów z raportem odrzuconych”** | nie wybrane | Mamy kontrolę typów w analizie (`kontrola_jakosci.md`, sekcja 3) i licznik „nierozpoznanych” w logu (0), ale nie zgłaszam tego jako rozszerzenia: nie ma osobnego raportu odrzuconych wartości w parserze. Rozszerzenia 4.0 realizujemy 4 inne. |

### 0.3 Rozstrzygnięte w tej fazie

| # | Punkt | Rozstrzygnięcie | Dowód |
|---|---|---|---|
| 1 | PDF laboratorium | Plik jest w `docs/LAB1.pdf`; sekcja 3 powtórzona wobec oryginału. | Sekcja 3. |
| 2 | Próg atrybutów | Dla PARSERA obowiązuje **18 atrybutów** i **200 rekordów** (4.0). **22 atrybuty i 400 rekordów to wymagania dla AUTORA** (5.0). Dane (26 atrybutów, 420 rekordów) spełniają oba. | PDF, „Zadanie na 4.0, Rola PARSER” oraz „Zadanie na 5.0, Rola AUTOR”; dopisek w `WYMAGANIA.md`. |
| 6 | Kod wyjścia 2 przy niedostępnym serwerze | **zrealizowany.** Autor wykonał ręcznie `python main.py --strony 1 --limit 1 --headless` przy zatrzymanym serwerze: komunikat „Serwis nie odpowiada pod adresem http://localhost:8000/ ...”, kod wyjścia 2, bez uruchamiania Chrome'a. Spójne z kodem (`cli.main`: `serwis_odpowiada` przed `otworz_driver`) i z testem `tests/test_cli.py`. Wynik pochodzi z relacji autora; nie powtarzałem próby (serwer uruchamia autor). | `docs/NOTATKI-DO-SPRAWOZDANIA.md`, sekcja „Faza 9”. |
| 10 | `matplotlib` poza stosem | Dopisany do stosu w `CLAUDE.md`. PDF też go zaleca („pandas + matplotlib (analiza)”). | `CLAUDE.md`, sekcja „Stos”. |
| 11 | Rozszerzenie opcjonalne (JSON w `dane/`) | Pomijamy (decyzja). Pozostaje w PDF-ie jako jedno z 7 rozszerzeń 5.0 do wyboru; nie jest wymagane przy spełnionych 2. | `WYMAGANIA.md`, sekcja „Opcjonalne”. |
| 12 | Checkboxy w `WYMAGANIA.md` | 28 punktów „zrealizowany” odhaczonych; niezaznaczone: opcjonalny JSON, blok sprawozdania (jest szkic `.md`, nie PDF) i „Oddanie”. | `WYMAGANIA.md`. |

## 1. Reguły z CLAUDE.md

| Reguła | Status | Dowód |
|---|---|---|
| `time.sleep` tylko w `utils/timing.py` | zrealizowany | `grep` po `bajtoparser/`, `main.py`, `tests/`, `analiza/`: jedyne `time.sleep` to `utils/timing.py:14` i `:28` (przypisanie `_czekaj = time.sleep`; wywołanie w `czekaj`, `timing.py:36`). Poza tym `import time` w `utils/logowanie.py:4` służy do `time.perf_counter` (zegar przebiegu, `logowanie.py:96`), nie do czekania. |
| Brak `import selenium` w `main.py`, `cli.py`, `pipeline.py` | zrealizowany | `grep selenium` w tych plikach zwraca tylko docstringi („bez selenium”). `main.py` zawiera wyłącznie `from bajtoparser.cli import main` i `sys.exit(main())`. Dodatkowo `eksport.py`, `porownanie.py` i `parsing/` bez importu selenium. |
| `cli.py` składa obiekty, ale nie zna selektorów | zrealizowany | `cli.py` importuje `CatalogPage`, `ProductPage`, `otworz_driver`; selektory są wyłącznie w `pages/catalog_page.py:81-92` i `pages/product_page.py:57-90` jako stałe na górze klasy. |
| `except Exception` tylko tam, gdzie uzasadnione | zrealizowany | Wszystkie wystąpienia w kodzie: `utils/diagnostyka.py:38,48,55` (diagnostyka nie może przykryć oryginalnego błędu; błąd tylko logowany) oraz `cli.py:183` (zamiana na kod wyjścia 2 z `log.exception`, komentarz w kodzie). Pozostałe `except` łapią konkretne typy (`ValueError`, `NoSuchElementException`, `URLError/OSError/ValueError`, `KeyboardInterrupt`, `WYJATKI_PONAWIANE`). Brak gołego `except:`. |
| Retry: tylko 3 wyjątki, backoff 1/2/4 s, limit prób | zrealizowany | `utils/retry.py`: `WYJATKI_PONAWIANE = (TimeoutException, StaleElementReferenceException, ElementClickInterceptedException)`; `ponawiaj()` łapie tylko ten zestaw. `timing.opoznienie_backoff` = `baza * 2**(n-1)`; `KONFIGURACJA.backoff_baza_s = 1.0`, `max_prob = 4` → 4 próby i opóźnienia 1, 2, 4 s. Testy: `tests/test_retry.py` (7), `tests/test_timing.py` (7). |
| Dekorator nie jest zagnieżdżany | zrealizowany | `@ponawiaj` na `BasePage.otworz`, `kliknij`, `CatalogPage.otworz_podstrone`, `wczytaj_porcje`, `ProductPage.otworz_produkt`, `otworz_zakladke`; docstringi opisują zakaz zagnieżdżania. |
| Diagnostyka `.png` + `.html` do `diagnostyka/`, potem wyjątek dalej | zrealizowany | `utils/diagnostyka.py: zapisz_diagnostyke`; wywołanie z `retry._zapisz_diagnostyke` dopiero po wyczerpaniu prób, potem `raise`. W `diagnostyka/` jest 8 plików (4 pary z 2026-10-11). Testy: `tests/test_diagnostyka.py` (5). |
| Synchronizacja tylko `WebDriverWait` + `expected_conditions` | zrealizowany | `pages/base_page.py:12-13,82` (`WebDriverWait`, `EC`); `czekaj_na_wzrost_atrybutu` czeka na wzrost `data-wczytano`, nie na migoczący `data-wczytywanie`. |
| Opóźnienie ≥ 0,5 s | zrealizowany | `MIN_PAUZA_GRZECZNOSCIOWA_S = 0.5` (`utils/konfiguracja.py:7`); `timing.pauza_grzecznosciowa` wymusza `max(zadana, 0.5)`; `cli.zbuduj_konfiguracje` podnosi mniejszą wartość z ostrzeżeniem; w logu: `pauza_s=0.5`. |
| Braki jako `None`/`NaN` | zrealizowany | `parsing/braki.py`; `okno.json`: 71 × `null` w `producent` (= 71 `—` w surowych); CSV: puste komórki, 0 znaków `—`. `nierozpoznane` = 0 w obu przebiegach. |
| Eksport CSV (UTF-8) i JSON (`force_ascii=False`) jednocześnie | zrealizowany | `eksport.py: eksportuj` zapisuje oba pliki jednym wywołaniem. `okno.csv`: bez BOM, UTF-8, 5134 polskich znaków, 0 mojibake, 0 U+FFFD. |
| Logowanie do pliku z podsumowaniem | zrealizowany | `utils/logowanie.py: skonfiguruj_logowanie`, `PodsumowaniePrzebiegu`; linia `PODSUMOWANIE:` ma tryb, stron, rekordów, błędów, retry, czas. Np. `logs/bajtoparser_20261013_001635.log`: stron=6, rekordów=420, błędów=0, retry=0, czas=351.59 s. |
| Type hints i docstringi po polsku | zrealizowany | Przejrzane pliki z `pages/`, `utils/`, `parsing/`, `cli.py`, `pipeline.py`, `eksport.py`, `porownanie.py`; `ruff check` czysty. Nie sprawdzałem wyczerpująco każdej funkcji (próbka: czytane moduły). |
| Nazwy po polsku konsekwentnie | częściowo | Dominuje polski (`ponawiaj`, `zapisz_diagnostyke`, `pobierz_rekordy`), ale zostają angielskie nazwy klas i modułów narzuconych przez POM (`BasePage`, `CatalogPage`, `ProductPage`, `pages/`, `pipeline.py`, `driver.py`, `retry.py`) oraz `Pipeline`. `CLAUDE.md` dopuszcza oba języki, o ile „konsekwentnie”; to mieszanka, ale spójna warstwowo. Ocena subiektywna. |

## 2. Punkty z WYMAGANIA.md

### Poziom 3.0
| Punkt | Status | Dowód |
|---|---|---|
| Jeden wiersz = jeden rekord, kolumna = atrybut | zrealizowany | `output/okno.csv`: 420 wierszy × 30 kolumn, 0 powtórzonych `id`; `parsing/rekord.py: KOLUMNY`. |
| Obie struktury w jednym formacie | zrealizowany | Kolumna `zrodlo`: tabela 178, karta 242 (razem 420 po deduplikacji; przed: 180 + 252 = 432). Jedna lista kolumn dla obu (`CatalogPage._JS_REKORDY`, `czysc_rekord`). |
| Cena jako liczba | zrealizowany | `cena` `float64`, `waluta` osobno (PLN 357, EUR 38, USD 25); 0 komórek z symbolem w `okno.json`; niezależny odczyt: 420/420 zgodnych (`kontrola_jakosci.md`, sekcja 4). |
| UTF-8, polskie znaki | zrealizowany | patrz „Eksport” w sekcji 1. |

### Poziom 4.0
| Punkt | Status | Dowód |
|---|---|---|
| ≥ 200 rekordów i ≥ 18 atrybutów | zrealizowany | 420 rekordów, 26 atrybutów serwisu (30 kolumn). Próg dla PARSERA to 18 atrybutów i 200 rekordów; 22 i 400 dotyczą AUTORA (sekcja 0.3, punkt 2). |
| Wszystkie podstrony + szczegóły, połączenie danych | zrealizowany | Log: „Podstron w serwisie: 6, do przetworzenia: 6”, `ze szczegółami=420`, `pominięte podstrony=-`. `CatalogPage.liczba_podstron`, `ProductPage.pobierz_szczegoly`, `pipeline.Pipeline.uruchom`. |
| Czyszczenie: liczby, formaty, duplikaty | zrealizowany | `parsing/ceny.py`, `daty.py`, `pola.py`, `duplikaty.py: deduplikuj` (po `id`, pierwsze wystąpienie). Log: 432 → 420 (usunięto 12). Daty ISO (0 naruszeń). Uwaga: nazewnictwo wymiarów to punkt 3 w sekcji 0.1, nie formaty. |
| Brak danych jako pusta wartość | zrealizowany | `producent` 71, `ocena` 84, `gwarancja_mies` 21, `waga_kg` 25 braków = `—` w surowych (zgodnie 1:1); `cena_poprzednia` 329 pustych = brak promocji. |
| Opóźnienie ≥ 0,5 s | zrealizowany | Sekcja 1. |

### Poziom 5.0
| Punkt | Status | Dowód |
|---|---|---|
| Selenium (Chrome) | zrealizowany | `utils/driver.py: utworz_driver` (`webdriver.Chrome`, `--headless=new`, `pl-PL`). |
| Jawne oczekiwanie | zrealizowany | Sekcja 1; w kodzie `pages/` brak `time.sleep`. |
| Doładowywanie do wyczerpania | zrealizowany | `CatalogPage.wczytaj_wszystko` + `wczytano_wszystko(porcja, porcji_lacznie)`; limit `MAKS_PORCJI = 20`. Wynik: 72 pozycje na każdej z 6 podstron (log). |
| Retry 1/2/4 s z limitem | zrealizowany | Sekcja 1. Zob. punkt 7 w sekcji 0.1 (nie zadziałał w pełnych przebiegach). |
| Porównanie surowy HTML vs DOM z liczbami i wnioskiem | zrealizowany | `output/okno_porownanie.json`: surowy HTML 0 `wiersz-produktu`, 0 `produkt`, 0 `data-id` na 6 podstronach (3952 B każda); DOM 432 pozycje (180 tabela + 252 karty) → 420 po deduplikacji; pole `wniosek`. `porownanie.py`, test `tests/test_porownanie.py` (16). Uwaga: „produkty z nazwą i id w treści: 0/10”. |

### Rozszerzenia
| Punkt | Status | Dowód |
|---|---|---|
| (4.0) Parametryzacja z CLI | zrealizowany | `cli.zbuduj_parser`: `--adres`, `--strony`, `--limit`, `--headless`, `--porownanie`, `--wyjscie`, `--katalog-wyjscia`, `--pauza`, `--timeout`. `tests/test_cli.py` (9). |
| (4.0) Eksport CSV + JSON jednocześnie | zrealizowany | `eksport.eksportuj`; `tests/test_eksport.py` (4); pliki `output/okno.{csv,json}`, `headless.{csv,json}`. |
| (4.0) Logowanie z podsumowaniem | zrealizowany | Sekcja 1; `tests/test_logowanie.py` (6). |
| (4.0) ≥ 3 testy funkcji czyszczących | zrealizowany | `tests/test_ceny.py` (7), `test_daty_braki.py` (6), `test_pola.py` (15), `test_duplikaty.py` (6), `test_rekord.py` (14): 48 testów czyszczenia; wszystkie 240 testów zielone, bez przeglądarki. |
| (5.0) Headless z pomiarem czasu w obu trybach | zrealizowany | okno 351,59 s, headless 410,30 s (linie `PRZEBIEG:`, logi `…001635` i `…002240`); wyniki identyczne (SHA-256 CSV, JSON, JSONL). Zob. punkt 9 w sekcji 0.1. |
| (5.0) Zrzut `.png` + `.html` przy błędzie | zrealizowany | Sekcja 1; `diagnostyka/` (8 plików). |
| Opcjonalne: źródło JSON w `dane/` | pominięte (decyzja) | Sekcja 0.3, punkt 11. |

### Analiza danych
| Punkt | Status | Dowód |
|---|---|---|
| Liczba rekordów, braki (szt., %) | zrealizowany | `kontrola_jakosci.md` sekcja 1 (420; 71/16,9%, 329/78,3%, 21/5,0%, 84/20,0%, 25/6,0%). |
| Duplikaty przed i po | zrealizowany | `kontrola_jakosci.md` sekcja 2 (432 → 420; 0 różnych od oryginału). Zastrzeżenie: punkt 5 w sekcji 0.1. |
| Typy kolumn | zrealizowany | sekcja 3: 30/30 zgodnych, 0 tekstu w kolumnach liczbowych. |
| Odstające z interpretacją | zrealizowany | sekcja 4 (IQR i z-score, każda cecha z interpretacją: anomalia vs błąd parsera). |
| Wniosek o parserze i co poprawiono | zrealizowany | sekcja 7: 0 niezgodności w 7980 porównaniach, brak zmian w `parsing/`; wymiary do potwierdzenia (punkt 3 w sekcji 0.1). |
| Średnia, mediana, moda, kwartyle, min, max | zrealizowany | `statystyki.md` sekcje 2-3. |
| Histogram (≥ 1), box-plot (≥ 1) | zrealizowany | `analiza/wykresy/hist_cena_pln.png`, `hist_ocena.png`, `box_cena_pln_kategoria.png`. |
| Korelacja ≥ 2 cech z komentarzem | zrealizowany | `statystyki.md` sekcja 5 (7 par, Pearson i Spearman, komentarz); `korelacje.png`. Zastrzeżenie: punkt 4 w sekcji 0.1. |

### Sprawozdanie i oddanie
| Punkt | Status | Dowód |
|---|---|---|
| Sprawozdanie (PDF), 6 sekcji | częściowo | Jest szkic `docs/SPRAWOZDANIE.md` (nie PDF). Sekcje z danymi uzupełnione, miejsca bez podstaw mają [DO UZUPEŁNIENIA]. |
| Archiwum ZIP na Delta | brak | Nie wykonane (zob. punkt 8 w sekcji 0.1). |
| Odpowiedź ustna | brak | Poza zakresem repozytorium. |

## 3. PDF laboratorium (`docs/LAB1.pdf`), rola PARSER: poziomy 3.0 / 4.0 / 5.0

Zweryfikowano wobec oryginału (tekst PDF wyciągnięty `pdftotext`, 185 linii). Punkty
poniżej są cytowane z PDF-a, a nie ze streszczenia w `WYMAGANIA.md`. Dowody: patrz sekcje 1-2.

### 3.0 (Rola PARSER)
| Punkt z PDF | Status | Dowód |
|---|---|---|
| Zapis do pliku CSV lub XLSX | zrealizowany | `output/okno.csv` (oraz `.json`); `eksport.eksportuj`. |
| Jeden wiersz = jeden rekord, jedna kolumna = jeden atrybut | zrealizowany | `okno.csv`: 420 wierszy × 30 kolumn, 0 powtórzonych `id`. |
| Minimum 60 wierszy z obu struktur, we wspólnym formacie | zrealizowany | 420 wierszy; `zrodlo`: tabela 178, karta 242; jedna lista `KOLUMNY`. |
| Cena jako liczba, nie tekst z symbolem waluty | zrealizowany | `cena` `float64`, `waluta` osobno; 0 komórek z symbolem w `okno.json`; odczyt niezależny 420/420 zgodnych. |
| UTF-8, poprawne polskie znaki | zrealizowany | `okno.csv`: bez BOM, 5134 polskich znaków, 0 mojibake, 0 U+FFFD. |
| Opóźnienie między żądaniami | zrealizowany | `timing.pauza_grzecznosciowa`, min. 0,5 s (`MIN_PAUZA_GRZECZNOSCIOWA_S`); w logu `pauza_s=0.5`. |
| (PDF: 3.0 nie wymaga sprawozdania ani odpowiedzi ustnej) | n/d | |

### 4.0 (Rola PARSER), wymagania obowiązkowe
| Punkt z PDF | Status | Dowód |
|---|---|---|
| Wszystko z poziomu 3.0 | zrealizowany | Tabela wyżej. |
| Minimum 200 rekordów i minimum 18 atrybutów | zrealizowany | 420 rekordów; 26 atrybutów serwisu (30 kolumn). Próg 22 dotyczy AUTORA (punkt 2). |
| Przejście przez wszystkie podstrony i wejście w podstrony szczegółów, łączenie danych | zrealizowany | Log: „Podstron w serwisie: 6, do przetworzenia: 6”, `ze szczegółami=420`. `CatalogPage.liczba_podstron`, `ProductPage.pobierz_szczegoly`. |
| Czyszczenie: ceny na liczby, ujednolicone formaty, usunięte duplikaty | zrealizowany | `parsing/ceny.py`, `daty.py`, `pola.py`, `duplikaty.deduplikuj`; log 432 → 420; daty ISO (0 naruszeń). |
| Brak danych jako pusta wartość, nie wyjątek | zrealizowany | `parsing/braki.py`; 71 `null` w `producent` = 71 `—` w surowych; 0 nierozpoznanych. |
| Opóźnienie minimum 0,5 s | zrealizowany | j.w. |

### 4.0 (Rola PARSER), rozszerzenia (min. 2 z listy)
| Pozycja listy z PDF | Wybrane | Status | Dowód |
|---|---|---|---|
| Walidacja typów kolumn i raport z liczbą odrzuconych | nie | n/d | Zob. P6. |
| Eksport do dwóch formatów jednocześnie (CSV oraz XLSX lub JSON) | **tak** | zrealizowany | `eksport.eksportuj`: CSV + JSON jednym wywołaniem; `tests/test_eksport.py` (4). |
| Logowanie do pliku z podsumowaniem (strony, rekordy, błędy, czas) | **tak** | zrealizowany | `logs/bajtoparser_20261013_001635.log`: stron=6, rekordów=420, błędów=0, czas=351.59 s. |
| Minimum 3 testy jednostkowe funkcji czyszczących | **tak** | zrealizowany | 48 testów czyszczenia (`test_ceny` 7, `test_daty_braki` 6, `test_pola` 15, `test_duplikaty` 6, `test_rekord` 14); 240 testów zielonych. |
| Pobieranie równoległe z limitem | nie | poza zakresem | Wykluczone w `WYMAGANIA.md`. |
| Parametryzacja z CLI (adres serwisu, liczba stron, plik wyjściowy) | **tak** | zrealizowany | `--adres`, `--strony`, `--wyjscie`, `--katalog-wyjscia` (+ `--limit`, `--headless`, `--pauza`, `--timeout`, `--porownanie`); `tests/test_cli.py` (9). |
| Własne rozszerzenie | nie | n/d | |

Wybrane 4 (wymagane 2): **spełnione z zapasem**.

### 4.0: analiza danych i sprawozdanie (wymagane od 4.0)
| Punkt z PDF | Status | Dowód |
|---|---|---|
| Liczba rekordów i braki w każdej kolumnie (szt. i %) | zrealizowany | `kontrola_jakosci.md`, sekcja 1 (420; 71/16,9%; 329/78,3%; 21/5,0%; 84/20,0%; 25/6,0%). |
| Duplikaty przed i po odrzuceniu | zrealizowany | sekcja 2 (432 → 420). Zastrzeżenie: punkt 5. |
| Typy kolumn: czy liczbowe są liczbowe | zrealizowany | sekcja 3: 30/30 zgodnych, 0 tekstu w kolumnach liczbowych. |
| Wartości odstające z interpretacją (anomalia czy błąd parsera, np. 129900 zamiast 1299) | zrealizowany | sekcja 4 (IQR i z-score, interpretacja każdej cechy) i test naiwnego `replace(",", ".")`; 0 przypadków zawyżenia 100× w danych. |
| Wniosek: co mówi o parserze i co poprawiono | zrealizowany | sekcja 7: 0 niezgodności w 7980 porównaniach, brak poprawek w `parsing/`. Otwarte: punkt 3 (nazwy wymiarów). |
| Średnia, mediana, moda, kwartyle, min, max | zrealizowany | `statystyki.md`, sekcje 2-3. |
| Histogram co najmniej jednej cechy | zrealizowany | `analiza/wykresy/hist_cena_pln.png`, `hist_ocena.png`. |
| Box-plot co najmniej jednej cechy | zrealizowany | `analiza/wykresy/box_cena_pln_kategoria.png`. |
| Korelacja ≥ 2 cech z komentarzem merytorycznym | zrealizowany | `statystyki.md`, sekcja 5 (7 par, Pearson i Spearman, komentarz); `korelacje.png`. Zastrzeżenie: punkt 4. |
| Odpowiedź ustna | n/d | Poza repozytorium. |

### 5.0 (Rola PARSER), wymagania obowiązkowe
| Punkt z PDF | Status | Dowód |
|---|---|---|
| Parser w oparciu o Selenium (bądź inne narzędzie) | zrealizowany | `utils/driver.py: utworz_driver` (Chrome). |
| Jawne oczekiwanie: WebDriverWait z warunkiem, nie sleep na sztywno | zrealizowany | `pages/base_page.py` (`WebDriverWait`, `expected_conditions`); `time.sleep` tylko w `utils/timing.py` (sekcja 1). |
| Obsługa doładowywania aż do wyczerpania rekordów | zrealizowany | `CatalogPage.wczytaj_wszystko`, `wczytano_wszystko`; 72 pozycje na każdej z 6 podstron. |
| Ponawianie z opóźnieniem wykładniczym (1 s, 2 s, 4 s…) i górnym limitem prób | zrealizowany | `utils/retry.ponawiaj`, `timing.opoznienie_backoff`; 4 próby; testy. Punkt 7: nie zadziałał w pełnych przebiegach. |
| W sprawozdaniu: porównanie liczby rekordów w surowym HTML i w DOM, z liczbami i wnioskiem | częściowo | Dane i wniosek są (`output/okno_porownanie.json`: 0 w surowym HTML, 432 pozycje w DOM po skryptach), sekcja 6.1 szkicu. „Częściowo”, bo sprawozdanie nie jest jeszcze w PDF (P4). |

### 5.0 (Rola PARSER), rozszerzenia (min. 2 z listy)
| Pozycja listy z PDF | Wybrane | Status | Dowód |
|---|---|---|---|
| Obsługa kodu 429 z Retry-After | nie | poza zakresem | Serwis nie ma takiego mechanizmu. |
| Zrzut ekranu i zapis źródła strony przy każdym błędzie | **tak** | zrealizowany | `utils/diagnostyka.zapisz_diagnostyke`; `diagnostyka/` (8 plików); `tests/test_diagnostyka.py` (5). Zob. uwaga poniżej. |
| Tryb headless z pomiarem czasu w obu trybach | **tak** | zrealizowany | okno 351,59 s, headless 410,30 s; wyniki identyczne (SHA-256). Punkt 9. |
| Wznawianie sesji (checkpoint) | nie | poza zakresem | Wykluczone w `WYMAGANIA.md`. |
| Porównanie czasu i pamięci: bez przeglądarki vs Selenium | nie | poza zakresem | Wykluczone w `WYMAGANIA.md`. |
| Wykrycie i użycie źródła danych (JSON) z omówieniem | nie | pominięte | Decyzja, punkt 11. |
| Własne rozszerzenie (uzgodnione z prowadzącym) | nie | n/d | |

Wybrane 2 (wymagane 2): **spełnione bez zapasu** (P1).

**Uwaga o zapisie przy błędzie.** PDF mówi „przy każdym błędzie”; kod zapisuje diagnostykę
po wyczerpaniu prób operacji (zgodnie z `CLAUDE.md`, zasada 4), a nie przy każdej nieudanej
próbie, żeby retry nie mnożył plików. Dla błędu, który kończy operację wyjątkiem, to spełnia
wymaganie; dla błędu przejściowego, który retry naprawił, plików nie ma. To świadoma decyzja
projektowa, nie niedopatrzenie, ale odbiega dosłownie od brzmienia PDF-a. Warto mieć to na
uwadze przy odpowiedzi ustnej.

### Sprawozdanie (wymagane od 4.0; „w formacie PDF”)
| Element z PDF | Status | Dowód / uwagi |
|---|---|---|
| Użyta technologia i uzasadnienie wyboru | częściowo | `SPRAWOZDANIE.md`, sekcja 1 (szkic). |
| Opis serwisu (rola AUTOR) | poza naszą rolą | Pominięte (P3); partner. |
| Opis parsera: rozszerzenia, selektory, dlaczego takie | częściowo | sekcja 2 (szkic). |
| Ocena odporności selektorów | częściowo | sekcja 3 (szkic; ocena rozumowa, bez pomiaru). |
| Wyniki kontroli jakości danych | częściowo | sekcja 4 (szkic). |
| Omówienie statystyk i wnioski | częściowo | sekcja 5 (szkic). |
| (5.0) Porównanie surowego HTML z drzewem DOM | częściowo | sekcja 6.1 (szkic). |
| Format PDF | brak | P4. |

„Częściowo” oznacza: treść jest w szkicu z liczbami z plików, brakuje wersji PDF i punktów
oznaczonych [DO UZUPEŁNIENIA].

### Oddanie
| Element z PDF | Status |
|---|---|
| Jedno archiwum na parę `LAB1_Nazwisko_Imie_Nazwisko_Imie.zip` na platformie Delta | brak (do wykonania; punkt 8) |
| Odpowiedź ustna na laboratoriach (4.0 i 5.0) | n/d |

### Wniosek
Wobec oryginału PDF poziom **5.0 dla roli PARSER jest spełniony technicznie**: wszystkie
wymagania obowiązkowe 3.0, 4.0 i 5.0 mają status „zrealizowany” (jedyny wyjątek to
porównanie HTML z DOM w sprawozdaniu, „częściowo” tylko z powodu braku PDF-a), rozszerzenia
4.0: 4 przy wymaganych 2, rozszerzenia 5.0: 2 przy wymaganych 2. Do zrobienia zostają
elementy organizacyjne: sprawozdanie w PDF (z opisem serwisu od partnera), archiwum ZIP i
odpowiedź ustna, oraz otwarty punkt 3 (nazwy wymiarów, do sprawdzenia z kluczem).
