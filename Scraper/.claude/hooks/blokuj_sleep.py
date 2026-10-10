"""Hook PreToolUse: odrzuca dodanie time.sleep w plikach .py poza bajtoparser/utils/timing.py.

Wykrywa `time.sleep` (także przy `import time as t`) oraz `from time import sleep`.
Komentarze i docstringi nie są liczone, bo analiza idzie przez AST. Gdy plik się
nie parsuje (np. w trakcie większej przeróbki), działa zapasowe wyrażenie regularne.
"""

from __future__ import annotations

import ast
import re

from wspolne import czesci_wzgledne, odrzuc, sciezka_pliku, tresc_przed_i_po, wczytaj_wejscie

DOZWOLONY_PLIK = ("bajtoparser", "utils", "timing.py")
WZORZEC_ZAPASOWY = re.compile(
    r"^[^#\n]*(\btime\s*\.\s*sleep\b|\bfrom\s+time\s+import\b[^#\n]*\bsleep\b)", re.MULTILINE
)


def policz_sleep(kod: str) -> int:
    """Zwraca liczbę użyć time.sleep (odwołań i importów) w kodzie źródłowym."""
    try:
        drzewo = ast.parse(kod)
    except SyntaxError:
        return len(WZORZEC_ZAPASOWY.findall(kod))

    aliasy_time = {"time"}
    for wezel in ast.walk(drzewo):
        if isinstance(wezel, ast.Import):
            aliasy_time |= {a.asname or a.name for a in wezel.names if a.name == "time"}

    licznik = 0
    for wezel in ast.walk(drzewo):
        if isinstance(wezel, ast.ImportFrom) and wezel.module == "time":
            licznik += sum(1 for a in wezel.names if a.name in ("sleep", "*"))
        elif (
            isinstance(wezel, ast.Attribute)
            and wezel.attr == "sleep"
            and isinstance(wezel.value, ast.Name)
            and wezel.value.id in aliasy_time
        ):
            licznik += 1
    return licznik


def main() -> None:
    """Sprawdza zmianę i blokuje ją, jeśli dokłada time.sleep w niedozwolonym pliku."""
    wejscie = wczytaj_wejscie()
    sciezka = sciezka_pliku(wejscie)
    if sciezka is None or sciezka.suffix != ".py":
        return
    czesci = czesci_wzgledne(sciezka, wejscie)
    if "venv" in czesci or czesci[-3:] == DOZWOLONY_PLIK:
        return

    przed, po = tresc_przed_i_po(wejscie)
    if policz_sleep(po) > policz_sleep(przed):
        odrzuc(
            f"Odrzucono zmianę w {sciezka.name}: time.sleep() jest dozwolone wyłącznie w "
            "bajtoparser/utils/timing.py (opóźnienie grzecznościowe i backoff retry). "
            "Na stan strony czekaj przez WebDriverWait + expected_conditions."
        )


if __name__ == "__main__":
    main()
