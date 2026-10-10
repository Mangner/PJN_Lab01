"""Testy deduplikacji rekordów po id."""

from bajtoparser.parsing.duplikaty import deduplikuj


def test_zostaje_pierwsze_wystapienie_i_liczba_usunietych() -> None:
    rekordy = [
        {"id": "P1", "nazwa": "pierwszy"},
        {"id": "P2", "nazwa": "drugi"},
        {"id": "P1", "nazwa": "duplikat"},
    ]
    unikalne, usuniete = deduplikuj(rekordy)
    assert unikalne == [{"id": "P1", "nazwa": "pierwszy"}, {"id": "P2", "nazwa": "drugi"}]
    assert usuniete == 1


def test_zachowuje_kolejnosc() -> None:
    rekordy = [{"id": i} for i in ("P3", "P1", "P2", "P1", "P3")]
    unikalne, usuniete = deduplikuj(rekordy)
    assert [r["id"] for r in unikalne] == ["P3", "P1", "P2"]
    assert usuniete == 2


def test_brak_duplikatow() -> None:
    unikalne, usuniete = deduplikuj([{"id": "P1"}, {"id": "P2"}])
    assert len(unikalne) == 2
    assert usuniete == 0


def test_pusta_lista() -> None:
    assert deduplikuj([]) == ([], 0)


def test_rekord_bez_id_nie_jest_usuwany() -> None:
    rekordy = [{"id": None, "nazwa": "a"}, {"nazwa": "b"}, {"id": "", "nazwa": "c"}]
    unikalne, usuniete = deduplikuj(rekordy)
    assert len(unikalne) == 3
    assert usuniete == 0


def test_nie_modyfikuje_wejscia() -> None:
    rekordy = [{"id": "P1"}, {"id": "P1"}]
    deduplikuj(rekordy)
    assert len(rekordy) == 2
