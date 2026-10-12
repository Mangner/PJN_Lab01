"""Wspólna konfiguracja: opóźnienia, retry, limity czasu, katalogi i parametry przebiegu."""

from dataclasses import dataclass
from pathlib import Path

MIN_PAUZA_GRZECZNOSCIOWA_S = 0.5


@dataclass(frozen=True)
class Konfiguracja:
    """Niemutowalny zestaw parametrów używanych przez `utils/`, `pages/` i pipeline.

    Pola przebiegu (`headless`, `strony`, `limit`, wyjście) ustawia CLI przez
    `dataclasses.replace`; `None` w `strony`/`limit` oznacza „wszystkie”.
    """

    pauza_s: float = MIN_PAUZA_GRZECZNOSCIOWA_S
    backoff_baza_s: float = 1.0
    max_prob: int = 4
    timeout_s: float = 10.0
    poll_s: float = 0.5
    szerokosc_okna: int = 1366
    wysokosc_okna: int = 900
    adres_serwisu: str = "http://localhost:8000/"
    katalog_logow: Path = Path("logs")
    katalog_diagnostyki: Path = Path("diagnostyka")
    headless: bool = False
    strony: int | None = None
    limit: int | None = None
    katalog_wyjscia: Path = Path("output")
    nazwa_wyjscia: str = "produkty"


KONFIGURACJA = Konfiguracja()
