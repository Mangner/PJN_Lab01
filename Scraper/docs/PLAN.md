# Plan pracy
Stan: odhaczaj po każdej fazie i rób commit. Każda faza to osobna sesja.

- [x] 0. Setup: venv, requirements, CLAUDE.md, docs, git, hooki
- [x] 1. Rekonesans: Claude ogląda serwis, zapisuje docs/SELEKTORY.md (bez kodu parsera)
- [ ] 2. Czyszczenie: testy najpierw, potem parsing/ (ceny, daty, braki)
- [ ] 3. Infrastruktura: BasePage, driver (--headless), retry, diagnostyka, logging
- [ ] 4. CatalogPage: doładowywanie do wyczerpania, tabela + karty
- [ ] 5. ProductPage: dwie zakładki, 13 atrybutów
- [ ] 6. Pipeline, CLI, eksport CSV + JSON
- [ ] 7. Pełne przebiegi (okno i headless) + porównanie surowy HTML vs DOM
- [ ] 8. Analiza jakości danych, poprawki parsera, statystyki i wykresy
- [ ] 9. Sprawozdanie PDF, audyt wymagań, archiwum ZIP