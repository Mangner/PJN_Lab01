"""Hook PreToolUse: odrzuca dodanie importu selenium w main.py, cli.py i pipeline.py.

Wykrywa `import selenium...` i `from selenium... import ...` przez AST; gdy plik się
nie parsuje, działa zapasowe wyrażenie regularne.
"""

from __future__ import annotations

import ast
import re

from wspolne import odrzuc, sciezka_pliku, tresc_przed_i_po, wczytaj_wejscie

CHRONIONE_PLIKI = {"main.py", "cli.py", "pipeline.py"}
WZORZEC_ZAPASOWY = re.compile(r"^\s*(from\s+selenium\b|import\s+[^#\n]*\bselenium\b)", re.MULTILINE)


def to_selenium(nazwa: str | None) -> bool:
    """Czy nazwa modułu to selenium albo jego podmoduł."""
    return nazwa is not None and (nazwa == "selenium" or nazwa.startswith("selenium."))


def policz_importy_selenium(kod: str) -> int:
    """Zwraca liczbę importów selenium w kodzie źródłowym."""
    try:
        drzewo = ast.parse(kod)
    except SyntaxError:
        return len(WZORZEC_ZAPASOWY.findall(kod))

    licznik = 0
    for wezel in ast.walk(drzewo):
        if isinstance(wezel, ast.Import):
            licznik += sum(1 for a in wezel.names if to_selenium(a.name))
        elif isinstance(wezel, ast.ImportFrom) and wezel.level == 0 and to_selenium(wezel.module):
            licznik += 1
    return licznik


def main() -> None:
    """Sprawdza zmianę i blokuje ją, jeśli dokłada import selenium w chronionym pliku."""
    wejscie = wczytaj_wejscie()
    sciezka = sciezka_pliku(wejscie)
    if sciezka is None or sciezka.name.lower() not in CHRONIONE_PLIKI:
        return

    przed, po = tresc_przed_i_po(wejscie)
    if policz_importy_selenium(po) > policz_importy_selenium(przed):
        odrzuc(
            f"Odrzucono zmianę w {sciezka.name}: main.py, cli.py i pipeline.py nie importują "
            "selenium (Strict Page Object Model). Interakcja z przeglądarką należy do "
            "bajtoparser/pages/, a fabryka sterownika do bajtoparser/utils/."
        )


if __name__ == "__main__":
    main()
