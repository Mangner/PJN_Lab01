"""Wspólne funkcje hooków PreToolUse (Write, Edit, MultiEdit).

Hook dostaje na stdin JSON z opisem narzędzia. Funkcje poniżej odtwarzają treść
pliku przed zmianą i po niej, żeby reguła mogła porównać liczbę naruszeń: zmiana
jest odrzucana tylko wtedy, gdy DODAJE naruszenie (poprawki istniejących przechodzą).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def wczytaj_wejscie() -> dict[str, Any]:
    """Wczytuje JSON hooka ze stdin (zawsze jako UTF-8, niezależnie od strony kodowej)."""
    sys.stderr.reconfigure(encoding="utf-8")
    return json.loads(sys.stdin.buffer.read().decode("utf-8"))


def sciezka_pliku(wejscie: dict[str, Any]) -> Path | None:
    """Zwraca ścieżkę edytowanego pliku albo None, gdy narzędzie jej nie podaje."""
    sciezka = wejscie.get("tool_input", {}).get("file_path")
    return Path(sciezka) if sciezka else None


def czesci_wzgledne(sciezka: Path, wejscie: dict[str, Any]) -> tuple[str, ...]:
    """Zwraca części ścieżki względem katalogu projektu, małymi literami."""
    projekt = Path(wejscie.get("cwd") or ".")
    try:
        wzgledna = sciezka.resolve().relative_to(projekt.resolve())
    except ValueError:
        wzgledna = sciezka
    return tuple(czesc.lower() for czesc in wzgledna.parts)


def tresc_przed_i_po(wejscie: dict[str, Any]) -> tuple[str, str]:
    """Odtwarza treść pliku przed zmianą i po niej dla Write, Edit i MultiEdit."""
    narzedzie = wejscie.get("tool_name", "")
    dane = wejscie.get("tool_input", {})
    sciezka = sciezka_pliku(wejscie)
    try:
        przed = sciezka.read_text(encoding="utf-8") if sciezka else ""
    except OSError:
        przed = ""

    if narzedzie == "Write":
        return przed, dane.get("content", "")

    edycje = dane.get("edits") if narzedzie == "MultiEdit" else [dane]
    po = przed
    for edycja in edycje or []:
        stary = edycja.get("old_string", "")
        nowy = edycja.get("new_string", "")
        if stary and stary in po:
            po = (
                po.replace(stary, nowy) if edycja.get("replace_all") else po.replace(stary, nowy, 1)
            )
        else:
            # Edycja i tak się nie powiedzie; sprawdzamy przynajmniej dopisywany fragment.
            po = po + "\n" + nowy
    return przed, po


def odrzuc(komunikat: str) -> None:
    """Blokuje wywołanie narzędzia: kod wyjścia 2, komunikat trafia do Claude'a."""
    print(komunikat, file=sys.stderr)
    sys.exit(2)
