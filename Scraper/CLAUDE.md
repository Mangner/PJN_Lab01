# Bajtoparser: scraper serwisu Bajtomarket (Laboratorium 1, rola PARSER, ocena 5.0)

Scraper lokalnego katalogu produktów. Serwis jest statyczną powłoką bez rekordów w surowym
HTML: wszystkie dane trafiają do DOM przez JavaScript (`fetch` plików JSON), więc potrzebna
jest przeglądarka (Selenium + Chrome). Serwis (`../Web-App/`) jest cudzy: nie edytujemy go
i nie czytamy `../Web-App/klucz/` (klucz odpowiedzi, którego używam dopiero do weryfikacji).

## Stos
Python 3.13, Selenium (Chrome, sterownik pobiera Selenium Manager), pandas, matplotlib
(wykresy w `analiza/`), markdown (tylko `sprawozdanie/buduj_pdf.py`), argparse, pytest, ruff. Brak innych zależności bez mojej zgody.

## Komendy
```powershell
venv\Scripts\Activate.ps1                        # aktywacja venv
python -m http.server 8000                        # serwis: osobny terminal, w ../Web-App
python main.py --strony 1 --limit 5               # szybki test na kilku rekordach
python main.py --headless                         # pełny przebieg bez okna
pytest                                            # testy funkcji czyszczących
ruff check . ; ruff format .                      # lint i formatowanie
```
Serwer uruchamiam sam. Jeśli nie odpowiada na http://localhost:8000/, powiedz mi o tym
zamiast próbować go uruchamiać.

## Architektura: Strict Page Object Model
```
main.py                 tylko wywołuje cli.main()
bajtoparser/
  cli.py                argparse, składanie obiektów, zero Selenium
  pipeline.py           logika sterująca: pętla po stronach i produktach, zapis
  pages/                BasePage, CatalogPage, ProductPage: cała interakcja z przeglądarką
  parsing/              czyste funkcje czyszczące (ceny, daty, braki), BEZ importu selenium
  utils/                driver (fabryka Chrome), retry, diagnostyka, timing, logging
tests/                  pytest dla parsing/ (bez przeglądarki)
```
- Selektory, klikanie, nawigacja i oczekiwania żyją WYŁĄCZNIE w `pages/`.
- `main.py`, `cli.py` i `pipeline.py` nie importują `selenium` i nie znają selektorów.
- Page Objecty zwracają surowe stringi i słowniki, bez czyszczenia. Czyszczenie jest w
  `parsing/` i da się je testować bez przeglądarki.
- Selektory trzymaj jako stałe na górze klasy strony. Preferuj semantyczne klasy i `data-*`
  (`.cena`, `data-id`) zamiast pozycji elementów i XPath.

## Żelazne zasady
1. **Synchronizacja z DOM tylko przez `WebDriverWait` + `expected_conditions`** na
   znacznikach stanu aplikacji. Żadnego `time.sleep()` do czekania na stronę.
2. `time.sleep()` wolno użyć wyłącznie w `utils/timing.py`: opóźnienie grzecznościowe
   ≥ 0,5 s między żądaniami i backoff dekoratora retry (1 s, 2 s, 4 s). Nigdzie indziej.
3. **Retry**: dekorator z backoffem wykładniczym i limitem prób. Łap tylko
   `TimeoutException`, `StaleElementReferenceException`, `ElementClickInterceptedException`,
   nigdy gołe `Exception`.
4. **Diagnostyka**: po wyczerpaniu prób zapisz zrzut `.png` i źródło `.html` do `diagnostyka/`,
   potem rzuć wyjątek dalej.
5. **Braki danych** (`—`) to `None` / `NaN`, nigdy wyjątek.
6. Eksport jednocześnie do `.csv` (UTF-8) i `.json` (`force_ascii=False`, polskie znaki).
7. Logowanie do pliku w `logs/` z podsumowaniem: liczba stron, rekordów, błędów, czas działania.
8. Type hints i docstringi po polsku; nazwy w kodzie po angielsku albo po polsku, ale
   konsekwentnie w całym projekcie.

## Znaczniki stanu serwisu (na nich oparte oczekiwania)
- `body[data-wczytano]`: ile rekordów pobrano dla podstrony
- `body[data-porcja]` i `body[data-porcji-lacznie]`: koniec doładowywania, gdy są równe
- `body[data-wczytywanie="tak"]`: trwa pobieranie porcji
- `body[data-stan-renderu="gotowy"]`: strona produktu ma dane
- `#panel-specyfikacja[data-wypelnione="tak"]`: zakładka *Specyfikacja* otwarta
- Panel *Dostawa i zwroty*: marker do potwierdzenia w DOM-ie, nie zgaduj go.

## Pułapki serwisu
- Flaga `data-wczytywanie` migocze przez 0,3–2 s. Nie czekaj na jej zmianę: zapamiętaj
  `data-wczytano` przed kliknięciem „Wczytaj więcej” i czekaj, aż wartość wzrośnie.
- Lista ma 6 podstron po 72 pozycje, ładowane porcjami po 12. Te same rekordy występują
  w tabeli (`table.tabela-ofert`) i w kartach (`article.produkt`): sprowadź je do wspólnego formatu.
- Ceny: `1 299,00 zł` (twarda spacja U+00A0), `246,99 €`, `$134.99`. Przecinek bywa
  separatorem dziesiętnym albo tysięcy. Nie używaj naiwnego `replace(",", ".")`.
- Pusta `cena_poprzednia` oznacza brak promocji, a nie brak danych. `—` z klasą
  `brak-wartosci` to brak danych (pola `producent`, `ocena`).
- Duplikaty: deduplikuj po `id` (celowo ~12 zduplikowanych rekordów na różnych podstronach).
- Daty na liście mają format `DD.MM.RRRR`.

## Sposób pracy
- Przed pracą przeczytaj: `docs/SERWIS.md` (mapa atrybutów i znaczniki), `docs/SELEKTORY.md`
  (jeśli istnieje) i `docs/PLAN.md` (aktualna faza). `docs/WYMAGANIA.md` czytaj przy zadaniach
  dotyczących zakresu lub audytu. Po zakończeniu fazy odhacz ją w PLAN.md i dopisz 2-3 zdania
  decyzji oraz konkretne liczby do `docs/NOTATKI-DO-SPRAWOZDANIA.md`.
- Większe zmiany zaczynaj od planu. Każde zadanie kończ weryfikacją (`pytest` lub
  `python main.py --strony 1 --limit 5`) i powiedz mi, co uruchomiłeś i co wyszło.
- Nie dodawaj funkcji spoza wymagań. Nie ruszaj `../Web-App/`.