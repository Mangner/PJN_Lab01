# Selektory serwisu Bajtomarket (faza 1: rekonesans)

Stan: zweryfikowano w DOM-ie przez Selenium (Chrome headless) na http://localhost:8000/,
`index.html`, `strona-2.html`, `produkt/P49235.html`, `produkt/P81619.html`.
Oznaczenia: **[DOM]** zweryfikowane w przeglądarce, **[README]** tylko z README/SERWIS.md.
Skrypty rekonesansowe: `scratch/rekonesans_*.py` (poza repozytorium).

## 1. Najważniejsze ustalenia
- Tabela i karty to **rozłączne zbiory**: na podstronie 30 wierszy tabeli + 42 karty = 72,
  zero wspólnych `data-id` **[DOM]**. Parser musi zebrać obie struktury, jedna nie wystarczy.
- Różnice tabela vs karty: w kartach każde pole ma prefiks `<span class="etykieta">`
  (tekst elementu to „Cena: 449,00 zł”), a karta bez promocji w ogóle nie ma elementu
  `.cena-poprzednia` (35 z 42), podczas gdy tabela ma pustą komórkę **[DOM]**.
- Marker panelu *Dostawa i zwroty*: `#panel-dostawa[data-wypelnione="tak"]`, identyczny
  jak dla Specyfikacji **[DOM]**.
- Surowy HTML nie zawiera żadnego rekordu (0), a `index.html` i `strona-2.html` są
  bajt w bajt tej samej wielkości (3952 B): powłoka + dwa skrypty **[DOM]**.

## 2. Lista (`index.html`, `strona-N.html`)
| element | selektor | status | dlaczego / odporność |
|---|---|---|---|
| wiersz tabeli | `tr.wiersz-produktu` | [DOM] | Klasa semantyczna, niezależna od pozycji. Przetrwa zmianę stylu, nie przetrwa zmiany nazwy klasy. |
| karta | `article.produkt` | [DOM] | Tag + klasa semantyczna. Jak wyżej. |
| id | atrybut `data-id` na wierszu/karcie | [DOM] | Atrybut danych to kontrakt z JS serwisu; najodporniejszy z możliwych, przeżyje zmianę układu. |
| nazwa, url | `a.odnosnik-produktu` (tekst, `href`) | [DOM] | Klasa semantyczna; `href` ma postać `/produkt/<id>.html`. |
| cena | `.cena` (tekst), waluta `data-waluta` | [DOM] | Waluta w atrybucie jest pewniejsza niż symbol z tekstu (PLN/EUR/USD). |
| cena_poprzednia | `.cena-poprzednia` | [DOM] | Tabela: pusta komórka; karta: element nieobecny. Oba = brak promocji. |
| kategoria, producent, dostepnosc, gwarancja | `.kategoria`, `.producent`, `.dostepnosc`, `.gwarancja` | [DOM] | Klasy nazwane po polu, te same w obu strukturach. |
| ocena, liczba_opinii, data_dodania | `.ocena`, `.liczba-opinii`, `.data-dodania` | [DOM] | Jak wyżej. Data `DD.MM.RRRR` [README], przykłady zgodne. |
| etykieta w karcie | `.etykieta` | [DOM] | Trzeba ją odciąć od wartości (np. usuwając prefiks tekstu w `pages/`). |
| kontenery | `#miejsce-tabeli`, `#miejsce-kart` (w `#sekcja-tabeli`, `#sekcja-kart`) | [DOM] | Id kontenerów z powłoki; pomocne do zawężania zakresu wyszukiwania. |

Wszystkie 13 atrybutów listy występuje w obu strukturach pod tymi samymi klasami **[DOM]**.
Pozycyjne selektory (`td:nth-child`, XPath) odpadają: kolejność kolumn tabeli nie jest
kontraktem, a klasy tak.

## 3. Doładowywanie („Wczytaj więcej”)
- Przycisk: `#wczytaj-wiecej` (`button.przycisk-glowny`, tekst „Wczytaj więcej”) **[DOM]**.
  Id jest stabilne i unikalne; tekst bywa zmienny, więc nie opieramy się na nim.
- Przebieg znaczników `body` (identyczny na `index.html` i `strona-2.html`) **[DOM]**:

| po kliknięciu | `data-wczytano` | `data-porcja` | `data-porcji-lacznie` |
|---|---|---|---|
| start | 12 | 1 | 6 |
| 1 | 24 | 2 | 6 |
| 2 | 36 | 3 | 6 |
| 3 | 48 | 4 | 6 |
| 4 | 60 | 5 | 6 |
| 5 | 72 | 6 | 6 |

- Po ostatniej porcji przycisk **nie znika z DOM**: tekst jest pusty, `is_displayed() = False`,
  brak atrybutu `disabled` **[DOM]**. Warunek końca: `data-porcja == data-porcji-lacznie`
  (i/lub `data-wczytano` przestaje rosnąć). `data-widocznych` = `data-wczytano` bez filtrów.
- `data-wczytywanie` w chwili pomiaru (po wzroście `data-wczytano`) było nieobecne **[DOM]**.
  Dalej obowiązuje zasada z CLAUDE.md: czekać na wzrost `data-wczytano`, nie na flagę.
- Wynik: 72 rekordy po wczytaniu wszystkich porcji jednej podstrony **[DOM]**, zgodnie z README.

## 4. Paginacja
- 6 podstron: linki `a[href*="strona-"]` z tekstem 2..6 oraz `Katalog` → `/` **[DOM]**.
  Na `index.html` widać linki 2-6; URL-e są przewidywalne (`strona-N.html`), więc nawigacja
  może iść po adresie, bez klikania. Na stronie są też linki do `dane/katalog.json` i `robots.txt`.

## 5. Strona produktu (`produkt/<id>.html`)
- Gotowość: `body[data-stan-renderu="gotowy"]`; `body[data-id]` = id produktu **[DOM]**.
- Zakładki: `button.zakladka[data-panel="opis|specyfikacja|dostawa"]` w `[role="tablist"]`,
  stan w `aria-selected` **[DOM]**. `data-panel` jest stabilnym kluczem, niezależnym od napisu.
- Panele: `#panel-opis` (widoczny od razu), `#panel-specyfikacja`, `#panel-dostawa`.
  Przed kliknięciem mają `hidden` i pusty `innerHTML`; po kliknięciu `hidden` znika,
  pojawia się `data-wypelnione="tak"` i `<dl>` **[DOM]**.
- Pola w panelach to `dd.<pole>` (nazwa klasy = nazwa pola) **[DOM]**:
  - Specyfikacja: `.ean`, `.kod-producenta`, `.kolor`, `.material`, `.waga`, `.wymiary`,
    `.kraj-pochodzenia` (`waga` i `wymiary` zawierają U+00A0).
  - Dostawa: `.sprzedawca`, `.stan-magazynowy`, `.czas-dostawy`, `.koszt-dostawy`, `.zwrot`.
- Opis: `#panel-opis` (tekst).
- Uwaga: odczyt `.text` z elementu w ukrytym panelu zwraca `''`. Pola czytać dopiero
  po otwarciu danej zakładki, a tekst brać z panelu widocznego (ewentualnie `textContent`).
- Nagłówek `#karta-produktu` **[DOM, faza 5]**: `h1#nazwa-produktu`, `p#identyfikator`
  („Symbol oferty: <id>”) i `dl.dane-podstawowe` z `dd.cena[data-waluta]`, `.kategoria`,
  `.producent`, `.dostepnosc`, `.ocena`, `.liczba-opinii`, `.data-dodania`, `.gwarancja`.
  Wszystkie to duplikaty pól z listy (te same klasy), bez nowych atrybutów, więc rekord
  szczegółów zostaje przy 13 kluczach. Nagłówek służy tylko do kontroli spójności
  (nazwa, kategoria) lista↔produkt.

## 6. Braki danych
- `—` z klasą `brak-wartosci` **[DOM]**:
  - tabela: `<td class="producent brak-wartosci">—</td>`
  - karta: `<p class="producent brak-wartosci"><span class="etykieta">Producent:</span> —</p>`
  - szczegóły produktu: `<dd class="producent brak-wartosci">—</dd>` (w nagłówku).
- Selektor braku: `.brak-wartosci` na elemencie pola; to wystarczy do zamiany na `None`.
- Na podstronie 1 (72 rekordy): 11 elementów `.brak-wartosci` w tabeli, 28 w kartach **[DOM]**.
- Pusta `cena_poprzednia` = brak promocji (nie brak danych): tabela 19 pustych komórek,
  karty 35 bez elementu **[DOM]**. W `pages/` oba przypadki sprowadzić do `""`/`None`.

## 7. Surowy HTML a DOM (do sprawozdania) **[DOM]**
Pobrane `urllib.request`, bez przeglądarki:

| plik | bajty | `tr.wiersz-produktu` | `article.produkt` | `data-id` | `<script>` |
|---|---|---|---|---|---|
| index.html | 3952 | 0 | 0 | 0 | 2 |
| strona-2.html | 3952 | 0 | 0 | 0 | 2 |
| produkt/P49235.html | 2770 | 0 | 0 | 0 | 2 |

W DOM po wykonaniu skryptów: 72 rekordy na podstronie (30 + 42). Wniosek: dane trafiają
do DOM wyłącznie przez JavaScript (`/statyczne/katalog.js`, `/statyczne/wspolne.js`),
więc bez przeglądarki lub bez użycia plików JSON nie da się ich pobrać.

## 8. Czego NIE zweryfikowano (tylko README)
- 12 duplikatów i 420 unikalnych rekordów (sprawdzono tylko podstrony 1 i 2 pod kątem struktur).
- Rozkład walut w całym katalogu (357 zł / 38 € / 25 $); na podstronie 1: PLN 63, EUR 5,
  USD 4 [DOM], co daje 72.
- Braki: 71 `producent`, 84 `ocena` w całości.
- Opóźnienie porcji 300-2000 ms (niemierzone).
