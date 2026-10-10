# Serwis Bajtomarket: ściąga dla parsera
Źródło: README kolegi. Serwis: http://localhost:8000/ (uruchamiany osobno).

## Skala
6 podstron (`index.html`, `strona-2.html` ... `strona-6.html`), po 72 pozycje (432 łącznie,
w tym 12 duplikatów, czyli 420 unikalnych). Podstrona wczytuje po 12 rekordów, 6 porcji,
przyciskiem „Wczytaj więcej”. Opóźnienie porcji: 300-2000 ms. Każdy produkt ma stronę
`produkt/<id>.html`.

## Lista: 13 atrybutów (te same w tabeli i kartach)
Dwie struktury na jednej podstronie: `table.tabela-ofert` (wiersz `tr.wiersz-produktu`)
i karty `article.produkt`.

| atrybut | gdzie |
|---|---|
| id | `data-id` na `tr.wiersz-produktu` / `article.produkt` / `a.odnosnik-produktu` |
| nazwa, url | `a.odnosnik-produktu`: treść i `href` |
| cena, waluta | `.cena`, waluta w `data-waluta` |
| cena_poprzednia | `.cena-poprzednia` (pusta = brak promocji, NIE brak danych) |
| kategoria, producent, dostepnosc, gwarancja | `.kategoria`, `.producent`, `.dostepnosc`, `.gwarancja` |
| ocena, liczba_opinii | `.ocena`, `.liczba-opinii` |
| data_dodania | `.data-dodania` (format `DD.MM.RRRR`) |

Brak danych (`producent`, `ocena`) wygląda jak `—` z klasą `brak-wartosci`.

## Strona produktu: 13 dodatkowych atrybutów
- Widoczny od razu: opis (`#panel-opis`)
- Zakładka *Specyfikacja* (po kliknięciu): ean, kod_producenta, kolor, material, waga,
  wymiary, kraj_pochodzenia
- Zakładka *Dostawa i zwroty* (po kliknięciu): sprzedawca, stan_magazynowy, czas_dostawy,
  koszt_dostawy, zwrot
- Razem 26 atrybutów (13 z listy + 13 ze szczegółów)

## Znaczniki stanu (podstawa WebDriverWait)
| znacznik | znaczenie |
|---|---|
| `body[data-wczytano]` | ile rekordów pobrano dla podstrony |
| `body[data-widocznych]` | ile rekordów jest na ekranie po filtrowaniu |
| `body[data-porcja]`, `body[data-porcji-lacznie]` | numer ostatniej porcji, liczba porcji |
| `body[data-wczytywanie="tak"]` | trwa pobieranie porcji (miga 0,3-2 s) |
| `body[data-stan-renderu="gotowy"]` | strona produktu ma dane |
| `#panel-specyfikacja[data-wypelnione="tak"]` | zakładka Specyfikacja wypełniona |
| panel Dostawa i zwroty | marker do ustalenia w DOM (nie zgadywać) |

## Pułapki
- Ceny: `1 299,00 zł` (twarda spacja U+00A0), `246,99 €`, `$134.99`. Przecinek raz jest
  separatorem dziesiętnym, raz tysięcy.
- Filtr kategorii i sortowanie przerysowują listę bez przeładowania. Parser nie używa
  filtrów, ale musi pamiętać, że `data-widocznych` może być mniejsze niż `data-wczytano`.
- Duplikaty: 12 rekordów, po dwa na podstronę, zawsze na innej podstronie niż oryginał.
- Kontrola poprawności (liczby README): waluty 357 zł / 38 € / 25 $, braki: 71 w `producent`,
  84 w `ocena`, 420 unikalnych rekordów.