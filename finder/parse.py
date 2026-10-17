"""Udtræk husleje, aconto, m², værelser, postnummer og faciliteter fra en annonces tekst."""
import re
from dataclasses import dataclass


@dataclass
class Details:
    rent: int | None = None
    aconto: int | None = None
    size: int | None = None
    rooms: float | None = None
    postcode: str | None = None
    unlimited: bool | None = None  # True = ubegrænset, False = tidsbegrænset
    limited_months: int | None = None
    dishwasher: bool | None = None  # None = ikke nævnt
    washer: bool | None = None


# Beløb som "10.895,-", "9.500 kr.", "13000 kr", "22.000,00 kr./md."
AMOUNT = r"(\d{1,3}(?:[.  ]\d{3})+|\d{3,6})(?:,\d{2}|,-)?\s*(?:kr|dkk|,-|-)?"


def _num(s: str) -> int:
    return int(re.sub(r"[.  ]", "", s))


def _amounts(label: str, text: str, skip_before=r"forudbetalt|depositum|indflytning"):
    """Alle beløb der står lige efter label, undtagen fx 'forudbetalt husleje'."""
    out = []
    for m in re.finditer(r"(" + label + r")[^\d\n]{0,30}?" + AMOUNT, text, re.I):
        before = text[max(0, m.start() - 15):m.start()].lower()
        if re.search(skip_before, before):
            continue
        n = _num(m.group(2))
        if 300 <= n <= 100_000 or "aconto" in label or "a/c" in label:
            out.append((m.group(1).lower(), n))
    return out


def _yes_no(label: str, text: str) -> bool | None:
    m = re.search(label + r"\s*:?\s*(ja|nej)\b", text, re.I)
    if m:
        return m.group(1).lower() == "ja"
    if re.search(r"(ingen|uden)\s+" + label, text, re.I):
        return False
    if re.search(label, text, re.I):
        return True
    return None


def parse(text: str) -> Details:
    t = re.sub(r"\s+", " ", text.replace("\xa0", " "))
    d = Details()

    rents = _amounts(r"m[åa]nedlig\s+leje|husleje(?:\s*\(mdl\.\))?|leje\s+pr\.?\s*m[åa]ned|\bleje\b", t)
    rents = [n for _, n in rents if n >= 2000]
    d.rent = rents[0] if rents else None

    # aconto: summér forskellige poster (varme, vand, forbrug); samme post tælles kun én gang
    acontos = {}
    for m in re.finditer(r"(?:aconto|a\s?conto|a/c)\s*(?:til\s+)?([a-zæøå/]*)[^\d\n]{0,20}?" + AMOUNT, t, re.I):
        n = _num(m.group(2))
        if 50 <= n <= 5000:
            acontos[m.group(1).lower() or "forbrug"] = n
    d.aconto = sum(acontos.values()) if acontos else None
    m = re.search(r"i alt pr\.? m[åa]ned\s*:?\s*" + AMOUNT, t, re.I)
    if d.aconto is None and d.rent and m and _num(m.group(1)) > d.rent:
        d.aconto = _num(m.group(1)) - d.rent

    m = (re.search(r"(?:bolig)?areal(?:\s*\(m2\))?\s*:?\s*(\d{2,3})(?:[.,]\d+)?", t, re.I)
         or re.search(r"(\d{2,3})(?:[.,]\d+)?\s*(?:m2|m²|kvm)", t, re.I))
    d.size = int(m.group(1)) if m else None

    m = (re.search(r"(?:antal\s+)?v[æa]relser\s*:?\s*(\d(?:[.,]5)?)\b", t, re.I)
         or re.search(r"\b(\d(?:[.,]5)?)\s*-?\s*(?:v(?:æ|a|ae)r(?:elses?|\.)|rums?\b)", t, re.I))
    d.rooms = float(m.group(1).replace(",", ".")) if m else None

    m = (re.search(r"postn(?:umme)?r\.?(?:\s+og\s+by)?\s*:?\s*(8\d{3})\b", t, re.I)
         or re.search(r"\b(8\d{3})\s+(?:Aarhus|Århus|Risskov|Viby|Højbjerg|Brabrand|Åbyhøj)", t, re.I))
    d.postcode = m.group(1) if m else None
    if not d.postcode:
        if re.search(r"Aarhus\s*C\b|Århus\s*C\b", t):
            d.postcode = "8000"
        elif re.search(r"Aarhus\s*N\b|Århus\s*N\b", t):
            d.postcode = "8200"

    m = re.search(r"tidsbegr[æa]ns\w*[^.\n]{0,60}?(\d{1,2})\s*(?:m[åa]ned|mdr)", t, re.I)
    if m:
        d.unlimited, d.limited_months = False, int(m.group(1))
    elif re.search(r"tidsbegr[æa]nsning\s*:?\s*ingen|lejeperiode\s*:?\s*ubegr[æa]nset|ubegr[æa]nset\s+lejem|tidsubegr[æa]nset", t, re.I):
        d.unlimited = True
    elif re.search(r"tidsbegr[æa]nset", t, re.I):
        d.unlimited = False
    elif re.search(r"ubegr[æa]nset", t, re.I):
        d.unlimited = True

    d.dishwasher = _yes_no(r"(?:opvaskemaskine|opvasker)", t)
    if re.search(r"f[æa]llesvaskeri|f[æa]lles\s+vaskeri", t, re.I) and not re.search(r"(?<!op)vaskemaskine|vaske-?\s*og\s*t[øo]rre", t, re.I):
        d.washer = False
    else:
        d.washer = _yes_no(r"(?:(?<!op)vaskemaskine|vaske-?\s*/?\s*t[øo]rremaskine)", t)
    return d
