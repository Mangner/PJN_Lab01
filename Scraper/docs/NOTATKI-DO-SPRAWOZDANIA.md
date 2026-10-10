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
