"""Wspólna konfiguracja infrastruktury: opóźnienia, retry, limity czasu, katalogi."""

from dataclasses import dataclass
from pathlib import Path

MIN_PAUZA_GRZECZNOSCIOWA_S = 0.5


@dataclass(frozen=True)
class Konfiguracja:
    """Niemutowalny zestaw parametrów używanych przez moduły `utils/` i `pages/`."""

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


KONFIGURACJA = Konfiguracja()
