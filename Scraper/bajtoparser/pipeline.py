"""Logika sterująca: pętla po stronach i produktach, zapis wyników (bez selenium).

Strony (Page Objecty) przychodzą przez konstruktor, więc pipeline da się testować na
atrapach. Polityka błędów jest tutaj: strony niczego nie połykają, a pipeline łapie
wyjątki, które zostają po wyczerpaniu retry (`WYJATKI_PONAWIANE`), liczy je i idzie dalej.
"""

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Protocol

from bajtoparser.eksport import eksportuj
from bajtoparser.parsing.duplikaty import deduplikuj, rozne_duplikaty
from bajtoparser.parsing.rekord import POLA_SZCZEGOLOW, czysc_rekord_z_kontrola, pola_listy
from bajtoparser.utils.konfiguracja import Konfiguracja
from bajtoparser.utils.logowanie import LICZNIK_RETRY, PodsumowaniePrzebiegu, nazwa_trybu
from bajtoparser.utils.retry import WYJATKI_PONAWIANE

log = logging.getLogger(__name__)


class StronaKatalogu(Protocol):
    """Interfejs strony katalogu używany przez pipeline (spełnia go `CatalogPage`)."""

    def otworz_podstrone(self, nr: int) -> None: ...
    def liczba_podstron(self) -> int: ...
    def wczytaj_wszystko(self) -> int: ...
    def pobierz_rekordy(self) -> list[dict[str, Any]]: ...


class StronaProduktu(Protocol):
    """Interfejs strony produktu używany przez pipeline (spełnia go `ProductPage`)."""

    def pobierz_szczegoly(self, url: str) -> dict[str, Any]: ...


class Pipeline:
    """Przebieg: lista z podstron → deduplikacja → szczegóły → czyszczenie → zapis.

    Każdy rekord (surowy, ze szczegółami) trafia od razu do `<wyjscie>_surowe.jsonl`,
    a na końcu (także po Ctrl+C albo awarii) oczyszczone rekordy idą do CSV i JSON.
    """

    CO_ILE_POSTEP = 25
    """Co ile produktów logować postęp."""

    ROZMIAR_PROBKI = 10
    """Ile pierwszych produktów trafia do próby porównania surowego HTML z DOM."""

    def __init__(
        self,
        strona_katalogu: StronaKatalogu,
        strona_produktu: StronaProduktu,
        konfiguracja: Konfiguracja,
    ) -> None:
        self.katalog = strona_katalogu
        self.produkt = strona_produktu
        self.konfiguracja = konfiguracja

    @property
    def sciezka_surowych(self) -> Path:
        """Plik zapisu w locie: `<katalog_wyjscia>/<nazwa_wyjscia>_surowe.jsonl`."""
        k = self.konfiguracja
        return Path(k.katalog_wyjscia) / f"{k.nazwa_wyjscia}_surowe.jsonl"

    def uruchom(self) -> PodsumowaniePrzebiegu:
        """Wykonuje cały przebieg i zwraca podsumowanie (zapisane też do logu).

        `KeyboardInterrupt` kończy przebieg czysto (`przerwano=True`). Inne wyjątki spoza
        `WYJATKI_PONAWIANE` (np. zamknięty Chrome) idą dalej, ale dopiero po eksporcie
        tego, co zebrano.
        """
        LICZNIK_RETRY.resetuj()
        podsumowanie = PodsumowaniePrzebiegu(tryb=nazwa_trybu(self.konfiguracja.headless))
        oczyszczone: list[dict[str, Any]] = []
        try:
            lista = self._zbierz_liste(podsumowanie)
            do_szczegolow = self._deduplikuj(lista, podsumowanie)
            self._przetworz_produkty(do_szczegolow, oczyszczone, podsumowanie)
        except KeyboardInterrupt:
            podsumowanie.przerwano = True
            log.warning("Przerwano przez użytkownika: zapisuję %d rekordów", len(oczyszczone))
        finally:
            podsumowanie.rekordy = len(oczyszczone)
            self._eksportuj(oczyszczone)
            podsumowanie.zakoncz()
            podsumowanie.zapisz_do_logu()
        return podsumowanie

    def _zbierz_liste(self, podsumowanie: PodsumowaniePrzebiegu) -> list[dict[str, Any]]:
        """Zbiera surowe rekordy z podstron 1..N; podstrona z błędem jest pomijana w całości.

        Błąd otwarcia podstrony 1 jest krytyczny (bez niej nie wiadomo, ile jest podstron).
        """
        self.katalog.otworz_podstrone(1)
        dostepne = self.katalog.liczba_podstron()
        limit = self.konfiguracja.strony
        liczba = dostepne if limit is None else min(limit, dostepne)
        podsumowanie.podstrony_w_serwisie = dostepne
        log.info("Podstron w serwisie: %d, do przetworzenia: %d", dostepne, liczba)

        rekordy: list[dict[str, Any]] = []
        for nr in range(1, liczba + 1):
            try:
                if nr > 1:
                    self.katalog.otworz_podstrone(nr)
                self.katalog.wczytaj_wszystko()
                z_podstrony = self.katalog.pobierz_rekordy()
            except WYJATKI_PONAWIANE as blad:
                podsumowanie.bledy += 1
                podsumowanie.pominiete_strony.append(nr)
                log.warning(
                    "Podstrona %d pominięta w całości (%s): brak jej rekordów w wyniku",
                    nr,
                    type(blad).__name__,
                )
                continue
            rekordy.extend(z_podstrony)
            podsumowanie.strony += 1
            log.info("Podstrona %d/%d: %d pozycji", nr, liczba, len(z_podstrony))
        podsumowanie.rekordy_lista = len(rekordy)
        podsumowanie.pozycje_zrodlo = dict(Counter(r.get("zrodlo") or "?" for r in rekordy))
        return rekordy

    def _deduplikuj(
        self, lista: list[dict[str, Any]], podsumowanie: PodsumowaniePrzebiegu
    ) -> list[dict[str, Any]]:
        """Usuwa duplikaty po `id` (przed wejściem w szczegóły) i przycina do `limit`."""
        unikalne, usuniete = deduplikuj(lista)
        rozne = rozne_duplikaty(lista, porownywane=pola_listy)
        podsumowanie.duplikaty = usuniete
        podsumowanie.rekordy_po_dedup = len(unikalne)
        podsumowanie.duplikaty_rozne = len(rozne)
        log.info("Deduplikacja: %d -> %d (usunięto %d)", len(lista), len(unikalne), usuniete)
        if rozne:
            log.warning(
                "Duplikaty różne od oryginału (%d), zostaje pierwsze wystąpienie: %s",
                len(rozne),
                ", ".join(map(str, rozne)),
            )
        limit = self.konfiguracja.limit
        wybrane = unikalne if limit is None else unikalne[:limit]
        podsumowanie.probka_produktow = [
            {"id": r.get("id"), "nazwa": r.get("nazwa"), "url": r.get("url")}
            for r in wybrane[: self.ROZMIAR_PROBKI]
        ]
        return wybrane

    def _przetworz_produkty(
        self,
        rekordy: list[dict[str, Any]],
        oczyszczone: list[dict[str, Any]],
        podsumowanie: PodsumowaniePrzebiegu,
    ) -> None:
        """Dla każdego rekordu: szczegóły, zapis surowego w locie, czyszczenie."""
        sciezka = self.sciezka_surowych
        sciezka.parent.mkdir(parents=True, exist_ok=True)
        with sciezka.open("w", encoding="utf-8") as plik:
            for nr, rekord in enumerate(rekordy, start=1):
                scalony = {**rekord, **self._szczegoly(rekord, podsumowanie)}
                plik.write(json.dumps(scalony, ensure_ascii=False) + "\n")
                plik.flush()

                czysty, nierozpoznane = czysc_rekord_z_kontrola(scalony)
                oczyszczone.append(czysty)
                if nierozpoznane:
                    podsumowanie.nierozpoznane += len(nierozpoznane)
                    log.warning(
                        "Rekord %s: nierozpoznane wartości w polach: %s",
                        rekord.get("id"),
                        ", ".join(nierozpoznane),
                    )
                if nr % self.CO_ILE_POSTEP == 0 or nr == len(rekordy):
                    log.info("Produkty: %d/%d", nr, len(rekordy))

    def _szczegoly(
        self, rekord: dict[str, Any], podsumowanie: PodsumowaniePrzebiegu
    ) -> dict[str, Any]:
        """Zwraca 13 surowych pól szczegółów; przy błędzie (po retry) same None i błąd w liczniku."""
        puste = dict.fromkeys(POLA_SZCZEGOLOW)
        url = rekord.get("url")
        if not url or not str(url).strip():
            podsumowanie.bledy += 1
            log.warning("Rekord %s: brak url, szczegóły pominięte", rekord.get("id"))
            return puste
        try:
            szczegoly = self.produkt.pobierz_szczegoly(url)
        except WYJATKI_PONAWIANE as blad:
            podsumowanie.bledy += 1
            log.warning(
                "Rekord %s: szczegóły niedostępne (%s), zostają dane z listy",
                rekord.get("id"),
                type(blad).__name__,
            )
            return puste
        podsumowanie.ze_szczegolami += 1
        return {**puste, **szczegoly}

    def _eksportuj(self, oczyszczone: list[dict[str, Any]]) -> None:
        """Zapisuje CSV i JSON; przy zerze rekordów nie nadpisuje poprzednich plików."""
        if not oczyszczone:
            log.warning("Brak rekordów do eksportu: pliki CSV i JSON nie zostały zapisane")
            return
        k = self.konfiguracja
        csv, json_ = eksportuj(oczyszczone, Path(k.katalog_wyjscia), k.nazwa_wyjscia)
        log.info("Zapisano %d rekordów: %s, %s", len(oczyszczone), csv, json_)
