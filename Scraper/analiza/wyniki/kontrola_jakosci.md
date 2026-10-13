# Kontrola jakości danych

Źródła: `output/okno.csv`, `output/okno_surowe.jsonl`, `output/headless.csv`,
`logs/bajtoparser_20261013_001635.log`. Raport generuje `python analiza/kontrola_jakosci.py`.

## 1. Liczba rekordów i braki

Liczba rekordów: **420**, kolumn: **30**.

Kolumna „puste w surowych” to liczba wartości `—` lub pustych w `okno_surowe.jsonl` dla tego samego pola: musi się zgadzać z brakami w CSV, inaczej parser zamieniałby coś w `NaN` bez powodu.

| kolumna | braków (szt.) | braków (%) | puste w surowych | uwaga |
|---|---|---|---|---|
| producent | 71 | 16.9 | 71 | znak „—” w surowych danych |
| cena_poprzednia | 329 | 78.3 | 329 | brak promocji, nie brak danych |
| gwarancja_mies | 21 | 5.0 | 21 | znak „—” w surowych danych |
| ocena | 84 | 20.0 | 84 | znak „—” w surowych danych |
| waga_kg | 25 | 6.0 | 25 | znak „—” w surowych danych |

Pozostałe 25 kolumn nie ma braków (pełna lista kolumn w tabeli typów poniżej).

## 2. Duplikaty przed i po odrzuceniu

| Etap | Liczba pozycji |
|---|---|
| Pozycje na liście przed deduplikacją (log) | 432 |
| Po deduplikacji po `id` (log) | 420 |
| Usunięte duplikaty (log) | 12 |
| Duplikaty różne od oryginału (log pipeline'u) | **0** |
| Rekordy w `okno.csv` | 420 |
| Powtórzone `id` w `okno.csv` | 0 |
| Powtórzone `url` w `okno.csv` | 0 |

Źródło liczb z logu: `logs/bajtoparser_20261013_001635.log` (linia `PODSUMOWANIE:`).

**Porównanie usuniętych duplikatów z oryginałem.** Pipeline porównał pola listy (po oczyszczeniu) każdego duplikatu z pierwszym wystąpieniem tego samego `id` jeszcze przed usunięciem: różnych było **0** z 12. Szczegóły (zakładki Specyfikacja i Dostawa) duplikatu są identyczne z założenia: duplikat ma to samo `id` i ten sam URL, więc prowadzi do tej samej strony produktu `produkt/<id>.html`, a jej treść nie zależy od tego, z której podstrony listy weszliśmy. Dlatego pipeline deduplikuje przed wejściem w szczegóły (duplikaty nie generują żądań). Ograniczenie: usunięte duplikaty nie są zapisane w żadnym pliku (`okno_surowe.jsonl` ma już tylko 420 linii), więc porównania nie da się powtórzyć z samych plików wyjściowych; opieramy się na liczbie z logu.

## 3. Typy kolumn

| kolumna | dtype | oczekiwany | zgodny |
|---|---|---|---|
| id | str | tekst | tak |
| nazwa | str | tekst | tak |
| url | str | tekst | tak |
| kategoria | str | tekst | tak |
| producent | str | tekst | tak |
| cena | float64 | liczbowy | tak |
| waluta | str | tekst | tak |
| cena_poprzednia | float64 | liczbowy | tak |
| dostepnosc | str | tekst | tak |
| gwarancja_mies | float64 | liczbowy | tak |
| ocena | float64 | liczbowy | tak |
| liczba_opinii | int64 | liczbowy | tak |
| data_dodania | str | tekst | tak |
| opis | str | tekst | tak |
| ean | str | tekst | tak |
| kod_producenta | str | tekst | tak |
| kolor | str | tekst | tak |
| material | str | tekst | tak |
| waga_kg | float64 | liczbowy | tak |
| dlugosc_cm | float64 | liczbowy | tak |
| szerokosc_cm | float64 | liczbowy | tak |
| wysokosc_cm | float64 | liczbowy | tak |
| kraj_pochodzenia | str | tekst | tak |
| sprzedawca | str | tekst | tak |
| stan_magazynowy_szt | int64 | liczbowy | tak |
| czas_dostawy_dni | int64 | liczbowy | tak |
| koszt_dostawy | float64 | liczbowy | tak |
| waluta_dostawy | str | tekst | tak |
| zwrot_dni | int64 | liczbowy | tak |
| zrodlo | str | tekst | tak |

Tekst w kolumnach liczbowych (niepuste komórki CSV, których nie da się zamienić na liczbę): **0**.

| Kontrola spójności | Rekordów naruszających |
|---|---|
| ean_nie_13_cyfr | 0 |
| ocena_poza_0_5 | 0 |
| ujemne_liczby | 0 |
| url_niezgodny_z_id | 0 |
| data_nie_iso | 0 |
| waluta_poza_zbiorem | 0 |
| znaki_zastepcze | 0 |

## 4. Wartości odstające

Metody: IQR (wartość poza [Q1 − 1,5·IQR; Q3 + 1,5·IQR]) oraz |z-score| > 3. Waluty analizowane osobno, bez przeliczania kursem.

| cecha | n | mediana | Q1 | Q3 | granica dolna | granica górna | odstające IQR | odstające \|z\|>3 | max |
|---|---|---|---|---|---|---|---|---|---|
| cena PLN | 357 | 309 | 149 | 849 | -901 | 1899 | 37 | 7 | 24999 |
| cena EUR | 38 | 60.99 | 23.49 | 235.24 | -294.13 | 552.87 | 2 | 1 | 786.99 |
| cena USD | 25 | 83.99 | 45.99 | 165.99 | -134.01 | 345.99 | 3 | 1 | 1769.99 |
| waga_kg | 395 | 1.46 | 0.36 | 3.15 | -3.81 | 7.33 | 47 | 11 | 38.5 |
| dlugosc_cm | 420 | 28 | 14 | 41 | -26.5 | 81.5 | 17 | 7 | 116 |
| szerokosc_cm | 420 | 21 | 8 | 37 | -35.5 | 80.5 | 45 | 9 | 191 |
| wysokosc_cm | 420 | 15 | 7 | 27.25 | -23.38 | 57.62 | 35 | 24 | 203 |
| liczba_opinii | 420 | 14 | 3 | 31 | -39 | 73 | 38 | 1 | 12480 |
| stan_magazynowy_szt | 420 | 52.5 | 2 | 144.5 | -211.75 | 358.25 | 0 | 0 | 250 |

### cena PLN

Odstających wg IQR: 37 (górnych: 37, dolnych: 0), wg z-score: 7. Największa wartość: 24999 (80.9× mediany). Kategorie odstających górnych: RTV i audio (12), Komputery (10), Sport i turystyka (7), AGD (4).

| id | kategoria | wartość | surowy napis |
|---|---|---|---|
| P25446 | AGD | 24999 | 24 999,00 zł |
| P63520 | Komputery | 9719 | 9 719,00 zł |
| P33745 | Komputery | 9159 | 9 159,00 zł |
| P97517 | RTV i audio | 8469 | 8 469,00 zł |
| P29771 | RTV i audio | 8349 | 8 349,00 zł |

**Interpretacja.** Prawostronny ogon rozkładu: drogi sprzęt (komputery, RTV, AGD, sport). Surowy napis daje dokładnie tę wartość, więc to **prawdziwa cecha danych, nie błąd parsera**.

### cena EUR

Odstających wg IQR: 2 (górnych: 2, dolnych: 0), wg z-score: 1. Największa wartość: 786.99 (12.9× mediany). Kategorie odstających górnych: Komputery (1), Sport i turystyka (1).

| id | kategoria | wartość | surowy napis |
|---|---|---|---|
| P54730 | Komputery | 786.99 | 786,99 € |
| P59116 | Sport i turystyka | 632.99 | 632,99 € |

**Interpretacja.** Prawostronny ogon rozkładu: drogi sprzęt (komputery, RTV, AGD, sport). Surowy napis daje dokładnie tę wartość, więc to **prawdziwa cecha danych, nie błąd parsera**.

### cena USD

Odstających wg IQR: 3 (górnych: 3, dolnych: 0), wg z-score: 1. Największa wartość: 1769.99 (21.1× mediany). Kategorie odstających górnych: Telefony i akcesoria (1), Sport i turystyka (1), RTV i audio (1).

| id | kategoria | wartość | surowy napis |
|---|---|---|---|
| P63694 | Telefony i akcesoria | 1769.99 | $1,769.99 |
| P28174 | Sport i turystyka | 1471.99 | $1,471.99 |
| P55586 | RTV i audio | 384.99 | $384.99 |

**Interpretacja.** Prawostronny ogon rozkładu: drogi sprzęt (komputery, RTV, AGD, sport). Surowy napis daje dokładnie tę wartość, więc to **prawdziwa cecha danych, nie błąd parsera**. Wartości z separatorem tysięcy (`$1,769.99`) są odczytane jako 1769.99, czyli poprawnie; to przypadek, na którym naiwny odczyt zawodzi (sekcja niżej).

### waga_kg

Odstających wg IQR: 47 (górnych: 47, dolnych: 0), wg z-score: 11. Największa wartość: 38.5 (26.4× mediany). Kategorie odstających górnych: Dom i ogród (18), RTV i audio (10), Sport i turystyka (10), Kuchnia (5).

| id | kategoria | wartość | surowy napis |
|---|---|---|---|
| P25446 | AGD | 38.5 | 38,5 kg |
| P79205 | Dom i ogród | 29 | 29 kg |
| P20819 | Dom i ogród | 28.88 | 28,88 kg |
| P34596 | Dom i ogród | 25.55 | 25,55 kg |
| P82261 | Dom i ogród | 24.34 | 24,34 kg |

**Interpretacja.** Ciężkie towary (dom i ogród, RTV, sport, AGD). Surowy napis (`38,5 kg`) daje tę samą liczbę; przecinek dziesiętny nie został wzięty za separator tysięcy (385 kg byłoby wartością absurdalną). **Anomalia danych (towary ciężkie), nie błąd parsera**.

### dlugosc_cm

Odstających wg IQR: 17 (górnych: 17, dolnych: 0), wg z-score: 7. Największa wartość: 116 (4.1× mediany). Kategorie odstających górnych: RTV i audio (17).

| id | kategoria | wartość | surowy napis |
|---|---|---|---|
| P21037 | RTV i audio | 116 | 116 x 54 x 10 cm |
| P90178 | RTV i audio | 113 | 113 x 63 x 7 cm |
| P71675 | RTV i audio | 108 | 108 x 56 x 10 cm |
| P56456 | RTV i audio | 104 | 104 x 8 x 10 cm |
| P58422 | RTV i audio | 104 | 104 x 61 x 9 cm |

**Interpretacja.** Duże i długie towary (telewizory i soundbary, lampy stojące, sprzęt sportowy). Wartości zgodne z surowym tekstem `a x b x c cm`, więc to **nie błąd przepisania**; wątpliwość dotyczy tylko tego, czy pozycja liczby w tekście odpowiada nazwie osi (patrz wniosek).

### szerokosc_cm

Odstających wg IQR: 45 (górnych: 45, dolnych: 0), wg z-score: 9. Największa wartość: 191 (9.1× mediany). Kategorie odstających górnych: Dom i ogród (23), AGD (11), Sport i turystyka (11).

| id | kategoria | wartość | surowy napis |
|---|---|---|---|
| P11495 | Dom i ogród | 191 | 36 x 191 x 47 cm |
| P25295 | Dom i ogród | 184 | 40 x 184 x 46 cm |
| P49195 | Dom i ogród | 179 | 46 x 179 x 39 cm |
| P85096 | Dom i ogród | 174 | 47 x 174 x 40 cm |
| P86097 | Dom i ogród | 171 | 42 x 171 x 40 cm |

**Interpretacja.** Duże i długie towary (telewizory i soundbary, lampy stojące, sprzęt sportowy). Wartości zgodne z surowym tekstem `a x b x c cm`, więc to **nie błąd przepisania**; wątpliwość dotyczy tylko tego, czy pozycja liczby w tekście odpowiada nazwie osi (patrz wniosek).

### wysokosc_cm

Odstających wg IQR: 35 (górnych: 35, dolnych: 0), wg z-score: 24. Największa wartość: 203 (13.5× mediany). Kategorie odstających górnych: Sport i turystyka (20), Dom i ogród (14), Kuchnia (1).

| id | kategoria | wartość | surowy napis |
|---|---|---|---|
| P10696 | Sport i turystyka | 203 | 71 x 1 x 203 cm |
| P20353 | Sport i turystyka | 198 | 58 x 99 x 198 cm |
| P12853 | Sport i turystyka | 195 | 56 x 96 x 195 cm |
| P32852 | Sport i turystyka | 192 | 55 x 1 x 192 cm |
| P29052 | Sport i turystyka | 190 | 69 x 1 x 190 cm |

**Interpretacja.** Duże i długie towary (telewizory i soundbary, lampy stojące, sprzęt sportowy). Wartości zgodne z surowym tekstem `a x b x c cm`, więc to **nie błąd przepisania**; wątpliwość dotyczy tylko tego, czy pozycja liczby w tekście odpowiada nazwie osi (patrz wniosek).

### liczba_opinii

Odstających wg IQR: 38 (górnych: 38, dolnych: 0), wg z-score: 1. Największa wartość: 12480 (891.4× mediany). Kategorie odstających górnych: Dom i ogród (7), Narzędzia (7), Zabawki (5), RTV i audio (4).

| id | kategoria | wartość | surowy napis |
|---|---|---|---|
| P86250 | Telefony i akcesoria | 12480 | 12480 |
| P86097 | Dom i ogród | 479 | 479 |
| P33745 | Komputery | 343 | 343 |
| P57069 | Kuchnia | 305 | 305 |
| P94875 | Narzędzia | 303 | 303 |

**Interpretacja.** Jedna wartość (12480) jest 26.1× większa od następnej (479) i jest jedynym odstającym wg z-score. Surowy napis to same cyfry (bez separatora, spacji i przecinka), więc parser nie miał jak jej zniekształcić. **Anomalia danych źródłowych, nie błąd parsera**; przy korelacjach raportować z nią i bez niej.

### stan_magazynowy_szt

Brak wartości odstających wg IQR (0 wg z-score). Zakres 0-250, zer: 90 (0 szt. to rzeczywisty stan magazynowy, a nie brak danych).

### Zgodność surowych napisów z oczyszczonymi wartościami (odczyt niezależny)

Odczyt prostym wyrażeniem regularnym, bez kodu z `parsing/`, porównany z CSV dla wszystkich
420 rekordów (tolerancja numeryczna 1e-9).

| kolumna | porównano | niezgodnych |
|---|---|---|
| cena | 420 | 0 |
| cena_poprzednia | 420 | 0 |
| ocena | 420 | 0 |
| gwarancja_mies | 420 | 0 |
| liczba_opinii | 420 | 0 |
| waga_kg | 420 | 0 |
| stan_magazynowy_szt | 420 | 0 |
| czas_dostawy_dni | 420 | 0 |
| zwrot_dni | 420 | 0 |
| koszt_dostawy | 420 | 0 |
| dlugosc_cm | 420 | 0 |
| szerokosc_cm | 420 | 0 |
| wysokosc_cm | 420 | 0 |
| data_dodania | 420 | 0 |
| waluta | 420 | 0 |
| producent | 420 | 0 |
| kategoria | 420 | 0 |
| nazwa | 420 | 0 |
| ean | 420 | 0 |

### Naiwny `replace(",", ".")` na rzeczywistych surowych cenach

Ilustracja na rzeczywistych surowych napisach z `okno_surowe.jsonl` (bez uruchamiania parsera). Naiwny odczyt: usunięcie `zł`, `€`, `$` i spacji (w tym U+00A0), potem `replace(",", ".")` i `float()`.

| waluta | rekordów | replace(",", ".") zgodne z parserem | wynik inny niż parser | ValueError | wariant: usunięcie przecinków, błędnych |
|---|---|---|---|---|---|
| PLN | 357 | 357 | 0 | 0 | 357 |
| EUR | 38 | 38 | 0 | 0 | 38 |
| USD | 25 | 23 | 0 | 2 | 0 |

Przypadki, w których naiwny `replace(",", ".")` daje wynik inny niż parser (do 3 na walutę):

| waluta | surowy napis | parser | naiwny replace(",", ".") | wariant: usunięcie przecinków |
|---|---|---|---|---|
| USD | $1,471.99 | 1471.99 | ValueError | 1471.99 |
| USD | $1,769.99 | 1769.99 | ValueError | 1769.99 |

**Co z tego wynika (dokładnie to, co wyszło z danych).** Dla PLN i EUR (przecinek dziesiętny) naiwny `replace(",", ".")` jest poprawny. Zawodzi tylko tam, gdzie przecinek jest separatorem tysięcy, czyli dla USD z tysiącami (`$1,299.00`): wynik to napis z dwiema kropkami (`1.299.00`) i `ValueError`, a nie cena zawyżona 100×. Zawyżenie ok. 100× daje dopiero inny naiwny wariant (usunięcie przecinków, żeby „pozbyć się separatora tysięcy”): ceny z przecinkiem dziesiętnym (PLN i EUR) są wtedy mnożone przez 100.

Przykłady wariantu z usunięciem przecinków (cena zawyżona 100×; `\xa0` w napisie to twarda spacja U+00A0):

| surowy napis | parser | usunięcie przecinków |
|---|---|---|
| 139,00\xa0zł | 139 | 13900 |
| 1\xa0529,00\xa0zł | 1529 | 152900 |
| 246,99\xa0€ | 246.99 | 24699 |

## 5. Zgodność z README serwisu

| miara | README | dane | zgodne |
|---|---|---|---|
| Pozycje na liście | 432 | 432 | tak |
| Unikalne rekordy (`id`) | 420 | 420 | tak |
| Duplikaty | 12 | 12 | tak |
| Waluta PLN | 357 | 357 | tak |
| Waluta EUR | 38 | 38 | tak |
| Waluta USD | 25 | 25 | tak |
| Braki w `producent` | 71 | 71 | tak |
| Braki w `ocena` | 84 | 84 | tak |

**Rozbieżności (README o nich nie wspomina):** `gwarancja_mies` ma 21 braków (5.0%); `waga_kg` ma 25 braków (6.0%). README podaje braki tylko dla `producent` i `ocena`. W surowych danych te braki to `—`, tak samo jak w polach z README, więc parser traktuje je prawidłowo jako `NaN` (kolumna „puste w surowych” w tabeli braków), a nie jako błąd.

## 6. Zgodność okno.csv z headless.csv

| plik | SHA-256 okno | SHA-256 headless | identyczne |
|---|---|---|---|
| CSV | 1a1ec910d87a69e9 | 1a1ec910d87a69e9 | True |
| JSON | c5ea19f4b011c384 | c5ea19f4b011c384 | True |
| JSONL (surowe) | 0d6a667d764d9e48 | 0d6a667d764d9e48 | True |

`DataFrame.equals` na `okno.csv` i `headless.csv`: **True** (420 × 30 vs 420 × 30). Hashe skrócone do 16 znaków.

## 7. Wniosek o poprawności parsera

- Typy kolumn: zgodne z oczekiwaniem.
- Kontrola spójności (EAN, zakres oceny, URL, daty, waluty, kodowanie): brak naruszeń.
- Braki w CSV vs `—` w surowych danych: zgodne.
- Niezależny odczyt surowych napisów vs CSV: **0** niezgodnych wartości w 7980 porównaniach.
- Liczby z README: wszystkie zgodne.
- okno vs headless: identyczne.

**Wniosek: nie znaleziono błędu parsera, więc nie wprowadzono zmian w `parsing/`.** Wartości odstające mają odpowiedniki w surowych napisach (odczyt niezależny dał te same liczby), więc są cechą danych serwisu, a nie artefaktem czyszczenia.

**Do weryfikacji z kluczem odpowiedzi (nie rozstrzygalne z samych danych):** kolejność liczb w `wymiary` (`17 x 9 x 8 cm`) jest w serwisie niepodpisana; parser przypisuje ją jako długość × szerokość × wysokość. Rozkłady (np. lampy stojące o „szerokości” rzędu 160–190 cm, telefony 7 × 14 × 1 cm) sugerują, że nazwy kolumn `dlugosc_cm`/`szerokosc_cm`/`wysokosc_cm` mogą nie odpowiadać znaczeniu tych liczb. Wartości są poprawnie przepisane, wątpliwe jest tylko nazewnictwo. Nie zmieniano go bez potwierdzenia.
