# Bajtomarket — serwis do sparsowania (Laboratorium nr 1, rola AUTOR, poziom 5.0)

Fikcyjny katalog 420 produktów. Serwis jest statyczny — wystarczy dowolny serwer plików —
ale cała treść listy i kart produktów powstaje w przeglądarce: w źródle HTML (Ctrl+U)
**nie ma ani jednego rekordu**, dane pochodzą z plików JSON pobieranych przez `fetch`.

## Uruchomienie

```bash
python -m http.server 8000
```

Następnie otwórz `http://localhost:8000/`. Nic poza Pythonem nie jest potrzebne — serwis nie ma
własnego backendu ani żadnej zależności zewnętrznej.

Dane są już wygenerowane. Jeżeli chcesz je zbudować od nowa (np. z innym ziarnem):

```bash
python generuj_serwis.py --ziarno 2026
```

Kontrola zgodności z wymaganiami laboratorium — działa na plikach, nie wymaga uruchomionego serwera:

```bash
python sprawdz_serwis.py
```

## Zawartość katalogu

| ścieżka | rola |
|---|---|
| `index.html`, `strona-2.html` … `strona-6.html` | powłoki 6 podstron katalogu (bez rekordów) |
| `produkt/<id>.html` | własna strona każdego z 420 rekordów (bez rekordu w źródle) |
| `dane/katalog.json` | metadane: podstrony, liczba porcji, kategorie, stan katalogu |
| `dane/strona-<n>-porcja-<k>.json` | porcje listy po 12 rekordów (36 plików) |
| `dane/produkt/<id>.json` | pełny rekord ze szczegółami (420 plików) |
| `szablony/` | szablony HTML, z których generator robi powłoki stron |
| `statyczne/` | arkusz stylów i trzy skrypty budujące stronę |
| `klucz/produkty_wzorcowe.csv` | **klucz odpowiedzi** — czyste wartości wszystkich pól |
| `klucz/duplikaty.csv` | wykaz celowo zduplikowanych rekordów |
| `generuj_serwis.py` | generator danych i całego serwisu (uruchamiany raz) |
| `sprawdz_serwis.py` | kontrola zgodności z wymaganiami |
| `_wersja-z-serwerem/` | wcześniejszy wariant z własnym serwerem — **nie jest częścią pracy**, można usunąć |

> `klucz/` służy do sprawdzenia parsera po jego napisaniu — nie przekazuj go partnerowi
> przed oddaniem pracy.

## Co dokładnie zrealizowano

### Wymagania obowiązkowe

| wymaganie | realizacja |
|---|---|
| ≥ 60 rekordów, ≥ 10 atrybutów | 420 rekordów, 26 atrybutów (13 na liście) |
| dwie różne struktury | `table.tabela-ofert` **oraz** karty `article.produkt` na tej samej podstronie |
| semantyczne nazwy klas | `produkt`, `cena`, `dostepnosc`, `data-dodania`, `wiersz-produktu`, `data-id` |
| paginacja ≥ 5 podstron, ≥ 200 rekordów | 6 podstron po 72 pozycje = 432 pozycje |
| podstrony szczegółów, ≥ 8 dodatkowych atrybutów | `produkt/<id>.html` — 13 atrybutów niedostępnych na liście |
| treść wstrzykiwana JavaScriptem | 0 rekordów w źródle HTML, wszystko przez `fetch` |
| doładowywanie porcjami | przycisk „Wczytaj więcej”, po 12 rekordów, 6 porcji na podstronę |
| ≥ 400 rekordów, ≥ 22 atrybuty | 420 rekordów, 26 atrybutów |
| opóźnienie 300–2000 ms | losowane przed pokazaniem każdej porcji (`statyczne/wspolne.js`) |

### Utrudnienia z poziomu 4.0 — wymagane 3, zrealizowano 3

1. **Ceny „1 299,00 zł”, a u części rekordów w innej walucie.** 357 rekordów w złotych
   (`1 299,00 zł` z twardą spacją U+00A0), 38 w euro (`246,99 €`) i 25 w dolarach
   (`$134.99`). Przecinek raz jest separatorem dziesiętnym, a raz separatorem tysięcy —
   naiwne `replace(",", ".")` zawyża cenę dolarową stukrotnie. To ten sam błąd, który
   kontrola jakości danych w sprawozdaniu ma wychwycić jako wartość odstającą.
2. **Braki wartości w dwóch polach u ponad 15% rekordów.** `producent` — 71 rekordów
   (16,9%), `ocena` — 84 rekordy (20,0%). W tabeli brak wygląda jak `—` z klasą
   `brak-wartosci`, w kartach tak samo; pusta komórka ceny poprzedniej to natomiast brak
   promocji, a nie brak danych — parser musi te dwa przypadki rozróżnić.
3. **12 zduplikowanych rekordów rozrzuconych po różnych podstronach**, po dwa na podstronę,
   zawsze na innej niż oryginał. Wykaz w `klucz/duplikaty.csv`.

### Utrudnienia z poziomu 5.0 — wymagane 2, zrealizowano 2

1. **Atrybuty widoczne dopiero po interakcji.** Na stronie produktu zakładka *Specyfikacja*
   (EAN, kod producenta, kolor, materiał, waga, wymiary, kraj pochodzenia) oraz *Dostawa
   i zwroty* (sprzedawca, stan magazynowy, czas i koszt dostawy, termin zwrotu) wypełniają
   się dopiero przy pierwszym kliknięciu. Przed interakcją oba panele są w DOM puste —
   łącznie 12 atrybutów jest nieosiągalnych bez kliknięcia.
2. **Filtrowanie i sortowanie zmieniające zawartość bez przeładowania strony.** Wybór
   kategorii albo porządku sortowania przerysowuje tabelę i karty z rekordów już wczytanych,
   bez nowego żądania i bez przeładowania dokumentu.

Reszta list wyboru została **celowo pominięta** — laboratorium wymaga zrealizowania
wskazanej liczby pozycji, a nie całej listy.

## Mapa atrybutów — gdzie czego szukać

Na liście katalogu (13 atrybutów, te same w tabeli i w kartach):

| atrybut | gdzie |
|---|---|
| `id` | `data-id` na `tr.wiersz-produktu` / `article.produkt` / `a.odnosnik-produktu` |
| `nazwa`, `url` | `a.odnosnik-produktu` — treść oraz `href` |
| `cena`, `waluta` | `.cena`, waluta w `data-waluta` |
| `cena_poprzednia` | `.cena-poprzednia` — pusta, gdy produkt nie jest w promocji |
| `kategoria`, `producent`, `dostepnosc`, `gwarancja` | `.kategoria`, `.producent`, `.dostepnosc`, `.gwarancja` |
| `ocena`, `liczba_opinii` | `.ocena`, `.liczba-opinii` |
| `data_dodania` | `.data-dodania` (format `DD.MM.RRRR`) |

Na stronie produktu dodatkowo 13 atrybutów, w tym 12 dopiero po kliknięciu zakładki:
`ean`, `kod_producenta`, `kolor`, `material`, `waga`, `wymiary`, `kraj_pochodzenia`
(*Specyfikacja*) oraz `sprzedawca`, `stan_magazynowy`, `czas_dostawy`, `koszt_dostawy`,
`zwrot` (*Dostawa i zwroty*). Opis produktu jest widoczny od razu, w `#panel-opis`.

Znaczniki stanu wygodne do `WebDriverWait`:

| znacznik | znaczenie |
|---|---|
| `body[data-wczytano]` | ile rekordów pobrano dla tej podstrony |
| `body[data-widocznych]` | ile rekordów jest na ekranie po filtrowaniu |
| `body[data-porcja]`, `body[data-porcji-lacznie]` | numer ostatniej porcji i ich łączna liczba |
| `body[data-wczytywanie="tak"]` | trwa pobieranie porcji |
| `body[data-stan-renderu="gotowy"]` | strona produktu ma już dane |
| `#panel-specyfikacja[data-wypelnione="tak"]` | zakładka została otwarta i wypełniona |

## Uwagi techniczne

- Skrypty są **zwykłe, nie modułowe**. `python -m http.server` bierze typ MIME z rejestru
  systemu i na części maszyn z Windowsem zwraca dla plików `.js` `text/plain`, co blokuje
  moduły ES. Zwykłe skrypty działają niezależnie od konfiguracji.
- Serwis trzeba otworzyć **przez serwer**, nie przez dwuklik na pliku. `fetch` na adresie
  `file://` jest blokowany przez politykę CORS, więc katalog pozostałby pusty.
- Dane są w całości fikcyjne i generowane deterministycznie (ziarno 2026), więc wynik
  `generuj_serwis.py` da się odtworzyć co do rekordu.

## Do sprawozdania

`sprawdz_serwis.py` wypisuje liczby, które wprost wchodzą do sprawozdania: liczbę rekordów
widocznych w surowym HTML (zero — żadna podstrona ani strona produktu nie zawiera nazwy
produktu ani identyfikatora), rozkład walut, udział braków w poszczególnych polach oraz
liczbę duplikatów. Zestawienie tego zera z liczbą rekordów w drzewie DOM po wykonaniu
skryptów to wymagane przez laboratorium porównanie HTML ↔ DOM.
