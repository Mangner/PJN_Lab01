## Opis serwisu

*Opis przygotowany na podstawie dokumentacji autora serwisu (Jakub Nawrocki).*

### Struktura serwisu

Bajtomarket to fikcyjny katalog 420 produktów. Serwis jest statyczny, ale cała treść listy
i kart produktów powstaje w przeglądarce: w źródle HTML nie ma ani jednego rekordu, a dane
pochodzą z plików JSON pobieranych przez `fetch`.

- **Podstrony katalogu:** 6 podstron (`index.html`, `strona-2.html` … `strona-6.html`) po 72
  pozycje, razem 432 pozycje (420 unikalnych rekordów).
- **Dwie struktury tej samej listy:** tabela `table.tabela-ofert` oraz karty
  `article.produkt` na jednej podstronie.
- **Doładowywanie:** przycisk „Wczytaj więcej”, porcje po 12 rekordów, 6 porcji na podstronę
  (36 plików JSON z porcjami). Przed pokazaniem każdej porcji serwis losuje opóźnienie
  300–2000 ms.
- **Strony produktów:** własna strona `produkt/<id>.html` dla każdego z 420 rekordów, także
  bez rekordu w źródle; pełne dane w `dane/produkt/<id>.json`.
- **Atrybuty:** 26, z czego 13 na liście i 13 dodatkowych na stronie produktu.

### Sposób generowania

Dane i cały serwis tworzy jednorazowo generator `generuj_serwis.py`. Dane są w całości
fikcyjne i generowane deterministycznie z ziarna 2026, więc wynik da się odtworzyć co do
rekordu. Generator uruchomiony z innym ziarnem buduje serwis od nowa.

### Zrealizowane utrudnienia

**Poziom 4.0 (wymagane 3, zrealizowano 3):**

1. *Ceny w różnych formatach i walutach.* 357 rekordów w złotych (`1 299,00 zł` z twardą
   spacją U+00A0), 38 w euro (`246,99 €`), 25 w dolarach (`$134.99`). Przecinek bywa
   separatorem dziesiętnym albo tysięcy, więc naiwne zastąpienie przecinka kropką zawyża
   cenę dolarową stukrotnie. Ten sam błąd kontrola jakości danych ma wychwycić jako wartość odstającą.
2. *Braki wartości w dwóch polach.* `producent` brakuje w 71 rekordach (16,9%), `ocena` w 84
   (20,0%); brak to `—` z klasą `brak-wartosci`. Pusta cena poprzednia oznacza brak
   promocji, nie brak danych, więc parser musi rozróżnić te przypadki.
3. *Duplikaty.* 12 zduplikowanych rekordów rozrzuconych po podstronach, po dwa na podstronę,
   zawsze na innej niż oryginał, co wymaga deduplikacji po całej liście.

**Poziom 5.0 (wymagane 2, zrealizowano 2):**

1. *Atrybuty widoczne dopiero po interakcji.* Zakładki *Specyfikacja* i *Dostawa i zwroty*
   wypełniają się przy pierwszym kliknięciu; wcześniej oba panele są w DOM puste, więc 12
   atrybutów jest nieosiągalnych bez kliknięcia.
2. *Filtrowanie i sortowanie bez przeładowania.* Wybór kategorii lub porządku przerysowuje
   tabelę i karty z rekordów już wczytanych, bez nowego żądania.

### Mapa atrybutów w skrócie

**Lista (13 atrybutów, te same w tabeli i kartach):** `id` (`data-id`), `nazwa` i `url`
(`a.odnosnik-produktu`), `cena` i `waluta` (`.cena`, `data-waluta`), `cena_poprzednia`,
`kategoria`, `producent`, `dostepnosc`, `gwarancja`, `ocena`, `liczba_opinii`
i `data_dodania` (format `DD.MM.RRRR`), każdy w klasie o tej samej nazwie.

**Strona produktu (13 dodatkowych atrybutów):** opis jest widoczny od razu (`#panel-opis`).
Pozostałe 12 pojawia się po kliknięciu zakładki: *Specyfikacja* (`ean`, `kod_producenta`,
`kolor`, `material`, `waga`, `wymiary`, `kraj_pochodzenia`) oraz *Dostawa i zwroty*
(`sprzedawca`, `stan_magazynowy`, `czas_dostawy`, `koszt_dostawy`, `zwrot`).

**Znaczniki stanu:** `body[data-wczytano]`, `body[data-widocznych]`, `body[data-porcja]`
i `body[data-porcji-lacznie]`, `body[data-wczytywanie="tak"]`, `body[data-stan-renderu="gotowy"]`
oraz `#panel-specyfikacja[data-wypelnione="tak"]`.
