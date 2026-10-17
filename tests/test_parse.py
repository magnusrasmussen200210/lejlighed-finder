from pathlib import Path

from finder.areas import classify
from finder.parse import parse

F = Path(__file__).parent / "fixtures"


def p(name):
    return parse((F / f"{name}.txt").read_text())


def test_taurus():
    d = p("taurus")
    assert (d.rent, d.aconto, d.size, d.rooms, d.postcode) == (10895, 700, 61, 2, "8000")
    assert d.unlimited and d.dishwasher and d.washer


def test_laros():
    d = p("laros")
    assert (d.rent, d.aconto, d.size, d.rooms, d.postcode) == (9500, 600, 55, 2, "8000")
    assert d.dishwasher and d.washer


def test_vidar():
    d = p("vidar")
    assert (d.rent, d.aconto, d.size, d.rooms, d.postcode) == (13000, 900, 106, 4, "8200")
    assert d.dishwasher and d.washer


def test_heimstaden():
    d = p("heimstaden")
    assert (d.size, d.rooms, d.postcode) == (48, 2, "8210")
    assert d.washer is False  # fællesvaskeri


def test_phoenix():
    d = parse((F / "phoenix.txt").read_text() + " find bolig/thunoegade 2, 2, 8000 aarhus c/")
    assert d.rent == 22000 and d.postcode == "8000"


def test_areas():
    assert classify("Herluf Trolles Gade 24 A, 8200 Aarhus N", "8200") == (1, "Trøjborg")
    assert classify("Jægergårdsgade 10, 8000 Aarhus C", "8000") == (2, "Frederiksbjerg")
    assert classify("Åhusene 3, 8000 Aarhus C", "8000") == (3, "Aarhus C")
    assert classify("Olof Palmes Allé 9U, 8200 Aarhus N", "8200") is None


def test_evaluate_and_message():
    from finder.main import evaluate, message
    from finder.sites import SITES
    from finder.application import render
    text = "Herluf Trolles Gade 24 A, st. tv. 8200 Aarhus N Husleje 8.200 kr. Aconto varme 500 kr. 52 m² 2 værelser Opvaskemaskine: Ja Lejeperiode: Ubegrænset"
    ok, area, d, flags = evaluate(text, text)
    assert ok and area == (1, "Trøjborg") and flags == []
    msg = message(SITES[0], "https://x", "Herluf Trolles Gade 24 A", area, d, flags, render("Herluf Trolles Gade 24 A", area[1], d))
    assert "8.700 kr" in msg and "Trøjborg" in msg
    assert not evaluate(text.replace("8.200", "9.800"))[0]  # over budget med aconto
