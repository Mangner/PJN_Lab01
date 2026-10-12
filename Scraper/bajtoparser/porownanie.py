"""Porównanie surowego HTML (bez przeglądarki) z DOM po wykonaniu skryptów.

Moduł pobiera strony przez `urllib`, więc widzi to, co serwer wysyła przed JavaScriptem.
Nie importuje `selenium` i nie zna selektorów przeglądarkowych: rekordy liczy po atrybucie
`data-id` oraz po klasach `wiersz-produktu` i `produkt` (osobno, po tokenach klasy).
Liczby DOM pochodzą z podsumowania przebiegu (`PodsumowaniePrzebiegu`), bez drugiej
przeglądarki. Błąd sieci nie przerywa porównania: strona dostaje `pobrano=False`.
"""

import json
import logging
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bajtoparser.utils import timing
from bajtoparser.utils.logowanie import PodsumowaniePrzebiegu

log = logging.getLogger(__name__)

KLASA_WIERSZ = "wiersz-produktu"
KLASA_KARTA = "produkt"
ATRYBUT_ID = "data-id"
TIMEOUT_DOMYSLNY_S = 10.0

Pobieracz = Callable[[str, float], str | None]
"""Funkcja `(url, timeout_s) -> tekst HTML albo None przy błędzie sieci`."""


@dataclass(frozen=True)
class AnalizaHtml:
    """Wynik analizy jednego dokumentu: liczniki i tekst treści (bez skryptów, stylów, noscript)."""

    wiersz_produktu: int = 0
    produkt: int = 0
    data_id: int = 0
    skrypty: int = 0
    wartosci_data_id: tuple[str, ...] = ()
    tekst: str = ""


class _Analizator(HTMLParser):
    """Zlicza klasy i atrybuty `data-id`; tekst zbiera poza `<script>`, `<style>`, `<noscript>`."""

    _POMIJANE = frozenset({"script", "style", "noscript"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.wiersz_produktu = 0
        self.produkt = 0
        self.skrypty = 0
        self.wartosci_data_id: list[str] = []
        self._tekst: list[str] = []
        self._pomijaj = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self.skrypty += 1
        if tag in self._POMIJANE:
            self._pomijaj += 1
        for nazwa, wartosc in attrs:
            if nazwa == "class" and wartosc:
                klasy = wartosc.split()
                self.wiersz_produktu += KLASA_WIERSZ in klasy
                self.produkt += KLASA_KARTA in klasy
            elif nazwa == ATRYBUT_ID:
                self.wartosci_data_id.append((wartosc or "").strip())

    def handle_endtag(self, tag: str) -> None:
        if tag in self._POMIJANE and self._pomijaj:
            self._pomijaj -= 1

    def handle_data(self, data: str) -> None:
        if not self._pomijaj:
            self._tekst.append(data)

    def wynik(self) -> AnalizaHtml:
        return AnalizaHtml(
            wiersz_produktu=self.wiersz_produktu,
            produkt=self.produkt,
            data_id=len(self.wartosci_data_id),
            skrypty=self.skrypty,
            wartosci_data_id=tuple(self.wartosci_data_id),
            tekst=" ".join(" ".join(self._tekst).split()),
        )


def analizuj_html(html: str) -> AnalizaHtml:
    """Liczy rekordy w surowym HTML; pusty lub uszkodzony dokument daje zera, nie wyjątek."""
    analizator = _Analizator()
    analizator.feed(html or "")
    analizator.close()
    return analizator.wynik()


def pobierz_html(url: str, timeout_s: float = TIMEOUT_DOMYSLNY_S) -> str | None:
    """Pobiera surowy HTML przez `urllib`; błąd sieci to `None` i ostrzeżenie w logu."""
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as odpowiedz:
            return odpowiedz.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, ValueError) as blad:
        log.warning("Pobranie %s nie powiodło się (%s): %s", url, type(blad).__name__, blad)
        return None


def adres_podstrony(adres_serwisu: str, nr: int) -> str:
    """Zwraca adres podstrony listy: `index.html` dla 1, `strona-N.html` dla N > 1."""
    if nr < 1:
        raise ValueError("numer podstrony musi być >= 1")
    baza = adres_serwisu.rstrip("/") + "/"
    return baza + ("index.html" if nr == 1 else f"strona-{nr}.html")


@dataclass(frozen=True)
class StronaHtml:
    """Liczby z jednej strony pobranej bez przeglądarki (`pobrano=False` przy błędzie sieci)."""

    url: str
    pobrano: bool
    bajty: int = 0
    wiersz_produktu: int = 0
    produkt: int = 0
    data_id: int = 0
    skrypty: int = 0
    id_produktu: str | None = None
    id_w_html: bool | None = None
    id_gdziekolwiek: bool | None = None
    nazwa_w_html: bool | None = None


@dataclass
class WynikPorownania:
    """Surowy HTML dla podstron listy i próby produktów."""

    podstrony: list[StronaHtml] = field(default_factory=list)
    produkty: list[StronaHtml] = field(default_factory=list)

    @property
    def bledy_sieci(self) -> int:
        """Liczba stron, których nie udało się pobrać."""
        return sum(not s.pobrano for s in (*self.podstrony, *self.produkty))

    def _suma(self, pole: str) -> int:
        return sum(getattr(s, pole) for s in self.podstrony if s.pobrano)

    @property
    def suma_wiersz_produktu(self) -> int:
        """Wystąpienia klasy `wiersz-produktu` na pobranych podstronach listy."""
        return self._suma("wiersz_produktu")

    @property
    def suma_produkt(self) -> int:
        """Wystąpienia klasy `produkt` na pobranych podstronach listy."""
        return self._suma("produkt")

    @property
    def suma_data_id(self) -> int:
        """Wystąpienia atrybutu `data-id` na pobranych podstronach listy."""
        return self._suma("data_id")

    @property
    def produkty_pobrane(self) -> int:
        """Ile stron produktów z próby udało się pobrać."""
        return sum(s.pobrano for s in self.produkty)

    @property
    def produkty_z_nazwa_i_id(self) -> int:
        """Ile pobranych stron produktów zawiera w surowym HTML i nazwę, i identyfikator."""
        return sum(bool(s.id_w_html and s.nazwa_w_html) for s in self.produkty if s.pobrano)


@dataclass(frozen=True)
class DaneDom:
    """Liczby z przebiegu przeglądarkowego (DOM) i jego parametry, do zestawienia z HTML."""

    tryb: str
    czas_s: float
    strony: int
    podstrony_w_serwisie: int
    pozycje_lista: int
    pozycje_tabela: int
    pozycje_karta: int
    po_deduplikacji: int
    rekordy_csv: int
    bledy: int
    retry: int
    ze_szczegolami: int

    @classmethod
    def z_podsumowania(cls, p: PodsumowaniePrzebiegu) -> "DaneDom":
        """Buduje dane DOM z podsumowania przebiegu (bez nowych żądań)."""
        return cls(
            tryb=p.tryb,
            czas_s=round(p.czas_s, 2),
            strony=p.strony,
            podstrony_w_serwisie=p.podstrony_w_serwisie,
            pozycje_lista=p.rekordy_lista,
            pozycje_tabela=p.pozycje_zrodlo.get("tabela", 0),
            pozycje_karta=p.pozycje_zrodlo.get("karta", 0),
            po_deduplikacji=p.rekordy_po_dedup,
            rekordy_csv=p.rekordy,
            bledy=p.bledy,
            retry=p.retry,
            ze_szczegolami=p.ze_szczegolami,
        )


def porownaj(
    adres_serwisu: str,
    liczba_podstron: int,
    probka: Sequence[Mapping[str, Any]],
    *,
    timeout_s: float = TIMEOUT_DOMYSLNY_S,
    pauza_s: float | None = None,
    pobieracz: Pobieracz = pobierz_html,
) -> WynikPorownania:
    """Pobiera podstrony 1..N i próbę produktów bez przeglądarki oraz liczy rekordy.

    `probka` to słowniki z kluczami `id`, `nazwa`, `url` (url względny albo pełny).
    Między żądaniami jest pauza grzecznościowa (nie przed pierwszym). Błąd sieci daje
    stronę z `pobrano=False`, nie wyjątek.
    """
    wynik = WynikPorownania()
    pierwsze = True

    def pobierz(url: str) -> str | None:
        nonlocal pierwsze
        if not pierwsze:
            timing.pauza_grzecznosciowa(pauza_s)
        pierwsze = False
        return pobieracz(url, timeout_s)

    for nr in range(1, liczba_podstron + 1):
        url = adres_podstrony(adres_serwisu, nr)
        html = pobierz(url)
        if html is None:
            wynik.podstrony.append(StronaHtml(url=url, pobrano=False))
            continue
        a = analizuj_html(html)
        wynik.podstrony.append(
            StronaHtml(
                url=url,
                pobrano=True,
                bajty=len(html.encode("utf-8")),
                wiersz_produktu=a.wiersz_produktu,
                produkt=a.produkt,
                data_id=a.data_id,
                skrypty=a.skrypty,
            )
        )

    baza = adres_serwisu.rstrip("/") + "/"
    for pozycja in probka:
        sciezka = pozycja.get("url")
        if not sciezka or not str(sciezka).strip():
            log.warning("Próba porównania: produkt %s bez url, pomijam", pozycja.get("id"))
            continue
        url = urljoin(baza, str(sciezka).strip())
        html = pobierz(url)
        if html is None:
            wynik.produkty.append(StronaHtml(url=url, pobrano=False))
            continue
        a = analizuj_html(html)
        id_produktu = pozycja.get("id")
        nazwa = pozycja.get("nazwa")
        wynik.produkty.append(
            StronaHtml(
                url=url,
                pobrano=True,
                bajty=len(html.encode("utf-8")),
                wiersz_produktu=a.wiersz_produktu,
                produkt=a.produkt,
                data_id=a.data_id,
                skrypty=a.skrypty,
                id_produktu=id_produktu,
                id_w_html=bool(
                    id_produktu and (id_produktu in a.wartosci_data_id or id_produktu in a.tekst)
                ),
                id_gdziekolwiek=bool(id_produktu and id_produktu in html),
                nazwa_w_html=bool(nazwa and " ".join(nazwa.split()) in a.tekst),
            )
        )
    return wynik


def wniosek(wynik: WynikPorownania, dom: DaneDom) -> str:
    """Jednozdaniowy wniosek wynikający z liczb (reguła, nie opis na sztywno)."""
    w_html = wynik.suma_wiersz_produktu + wynik.suma_produkt + wynik.suma_data_id
    if not any(s.pobrano for s in wynik.podstrony):
        return "Brak pobranych podstron: porównanie niemożliwe."
    if w_html == 0 and dom.pozycje_lista > 0:
        return (
            "Surowy HTML nie zawiera żadnego rekordu, a DOM po skryptach "
            f"{dom.pozycje_lista} pozycji: dane są wstrzykiwane wyłącznie przez JavaScript, "
            "więc samo pobranie HTML (urllib) nie wystarczy, potrzebna jest przeglądarka."
        )
    if w_html > 0:
        return (
            f"Surowy HTML zawiera rekordy ({wynik.suma_wiersz_produktu} wierszy, "
            f"{wynik.suma_produkt} kart) przy {dom.pozycje_lista} pozycjach w DOM: "
            "porównaj liczby, część danych jest dostępna bez przeglądarki."
        )
    return "Brak rekordów zarówno w surowym HTML, jak i w DOM."


def linia_porownania(wynik: WynikPorownania, dom: DaneDom) -> str:
    """Zestawienie w jednej linii do logu i podsumowania."""
    return (
        f"POROWNANIE: DOM: lista={dom.pozycje_lista} (tabela {dom.pozycje_tabela} / "
        f"karty {dom.pozycje_karta}), po deduplikacji={dom.po_deduplikacji}, "
        f"CSV={dom.rekordy_csv} | surowy HTML ({len(wynik.podstrony)} podstron): "
        f"wiersz-produktu={wynik.suma_wiersz_produktu}, produkt={wynik.suma_produkt}, "
        f"data-id={wynik.suma_data_id}; produkty z nazwą i id: "
        f"{wynik.produkty_z_nazwa_i_id}/{wynik.produkty_pobrane} "
        f"(błędów sieci: {wynik.bledy_sieci})"
    )


def zapisz_json(wynik: WynikPorownania, dom: DaneDom, katalog: Path, nazwa: str) -> Path:
    """Zapisuje `<katalog>/<nazwa>_porownanie.json` (UTF-8, polskie znaki bez escapowania)."""
    katalog = Path(katalog)
    katalog.mkdir(parents=True, exist_ok=True)
    sciezka = katalog / f"{nazwa}_porownanie.json"
    tresc = {
        "raw_html": {
            "podstrony": [asdict(s) for s in wynik.podstrony],
            "produkty": [asdict(s) for s in wynik.produkty],
            "suma_wiersz_produktu": wynik.suma_wiersz_produktu,
            "suma_produkt": wynik.suma_produkt,
            "suma_data_id": wynik.suma_data_id,
            "produkty_z_nazwa_i_id": wynik.produkty_z_nazwa_i_id,
            "produkty_pobrane": wynik.produkty_pobrane,
            "bledy_sieci": wynik.bledy_sieci,
        },
        "dom": asdict(dom),
        "wniosek": wniosek(wynik, dom),
    }
    sciezka.write_text(json.dumps(tresc, ensure_ascii=False, indent=2), encoding="utf-8")
    return sciezka
