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
