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


def test_newlines_and_ae():
    d = parse("Økonomi\nHusleje\n10.245 kr\nA/C (Aconto)\n750 kr\n2 rum\n51 m²\nThomas Koppels Gade 90, 10. 3\n8000 Aarhus C")
    assert (d.rent, d.aconto, d.rooms, d.size, d.postcode) == (10245, 750, 2, 51, "8000")
    d = parse("Husleje (Mdl.) :\n11.195,-\nA/C forbrug :\n600,-\nForudbetalt leje: 10.995,-")
    assert (d.rent, d.aconto) == (11195, 600)


def test_senior():
    from finder.main import evaluate
    ok, *_ = evaluate("Teglgårdens virkeboliger - for lejere der er +50 år, 8000 Aarhus C, Husleje 8.000 kr, 2 vær., 60 m²")
    assert not ok


def test_propstep_total():
    d = parse("Økonomi Husleje 13.895,00 Varme 600,00 Vand 350,00 El Direkte afregning I alt pr. måned 14.845,00 Depositum 41.685,00")
    assert (d.rent, d.aconto) == (13895, 950)


def test_application_has_no_placeholders(monkeypatch):
    from finder.application import render
    from finder.parse import Details
    tpl = Path("/mnt/project-files/lejlighed/ansoegning-secret.txt")
    if tpl.exists():
        monkeypatch.setenv("ANSOEGNING", tpl.read_text())
    monkeypatch.setenv("KONTAKT_TELEFON", "31180445")
    monkeypatch.setenv("KONTAKT_EMAIL", "test@example.com")
    for area in ("Trøjborg", "Frederiksbjerg", "Aarhus C"):
        out = render("Åhusene 3, 2. 3, 8000 Aarhus C", area, Details(dishwasher=True))
        assert "{" not in out and "}" not in out
        assert "Åhusene 3" in out and "31180445" in out
    monkeypatch.setenv("ANSOEGNING", "Hej {adresse}\n{stavet_forkert}\nHilsen")
    assert render("X", "Aarhus C", Details()) == "Hej X\nHilsen"


def test_pick_recipient():
    from finder.mailer import pick_recipient
    assert pick_recipient("Kontakt Amanda arp@dacas.dk 60 38 Mail: dacas@dacas.dk") == "arp@dacas.dk"
    assert pick_recipient("Kontakt aarhus@lejeboligmaegleren.dk") == "aarhus@lejeboligmaegleren.dk"
    assert pick_recipient("Malthe Email: mkj@taurus.dk ... taurus@taurus.dk") == "mkj@taurus.dk"
    assert pick_recipient("ingen mail her") is None


def test_dac_unlimited():
    assert parse("Tidsbegrænsning: Ingen Månedlig husleje: 8.250 kr. Månedlig aconto: 600 kr.").unlimited is True
