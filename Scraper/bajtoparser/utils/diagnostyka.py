"""Diagnostyka błędów: zrzut ekranu (.png) i źródło strony (.html) do `diagnostyka/`.

Funkcje z tego modułu nigdy nie rzucają wyjątków: błąd zapisu jest tylko logowany,
żeby nie przykryć oryginalnego błędu, który wywołał diagnostykę.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from bajtoparser.utils.konfiguracja import KONFIGURACJA

log = logging.getLogger(__name__)

_NIEDOZWOLONE_W_NAZWIE = re.compile(r"[^A-Za-z0-9_-]+")


def nazwa_bazowa(operacja: str, kiedy: datetime | None = None) -> str:
    """Buduje nazwę pliku bez rozszerzenia: `RRRRMMDD_GGMMSS_mmm_<operacja>`."""
    kiedy = kiedy or datetime.now()
    znacznik = kiedy.strftime("%Y%m%d_%H%M%S_") + f"{kiedy.microsecond // 1000:03d}"
    slug = _NIEDOZWOLONE_W_NAZWIE.sub("_", operacja).strip("_")[:60] or "operacja"
    return f"{znacznik}_{slug}"


def zapisz_diagnostyke(
    driver: Any, operacja: str, katalog: Path | None = None
) -> tuple[Path | None, Path | None]:
    """Zapisuje zrzut `.png` i źródło `.html`; zwraca ścieżki (`None` dla nieudanego zapisu)."""
    png: Path | None = None
    html: Path | None = None
    try:
        cel = Path(katalog) if katalog is not None else KONFIGURACJA.katalog_diagnostyki
        cel.mkdir(parents=True, exist_ok=True)
        baza = nazwa_bazowa(operacja)
    except Exception:
        log.exception("Diagnostyka: nie udało się przygotować katalogu")
        return None, None

    try:
        sciezka = cel / f"{baza}.png"
        if driver.save_screenshot(str(sciezka)):
            png = sciezka
        else:
            log.error("Diagnostyka: zapis zrzutu ekranu nie powiódł się: %s", sciezka)
    except Exception:
        log.exception("Diagnostyka: błąd zapisu zrzutu ekranu")

    try:
        sciezka = cel / f"{baza}.html"
        sciezka.write_text(driver.page_source, encoding="utf-8")
        html = sciezka
    except Exception:
        log.exception("Diagnostyka: błąd zapisu źródła strony")

    log.error("Diagnostyka operacji %r: png=%s, html=%s", operacja, png, html)
    return png, html
