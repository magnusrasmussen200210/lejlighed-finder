"""Udtræk husleje, aconto, m², værelser, postnummer og faciliteter fra en annonces tekst."""
import re
from dataclasses import dataclass, field


@dataclass
class Details:
    rent: int | None = None
    aconto: int | None = None
    size: int | None = None
    rooms: float | None = None
    postcode: str | None = None
    unlimited: bool | None = None  # True = ubegrænset, False = tidsbegrænset
    limited_months: int | None = None
    dishwasher: bool = False
    washer: bool = False
    street: str | None = None
    notes: list[str] = field(default_factory=list)


def _num(s: str) -> int:
    return int(re.sub(r"[.\s ]", "", s.split(",")[0]))


AMOUNT = r"(\d{1,3}(?:[.\s ]\d{3})+|\d{3,6})(?:,\d{2}|,-)?\s*(?:kr|dkk)"


def _amount_after(label: str, text: str) -> int | None:
    m = re.search(label + r"[^\d\n]{0,40}?" + AMOUNT, text, re.I)
    return _num(m.group(1)) if m else None


def parse(text: str) -> Details:
    t = text.replace("\xa0", " ")
    d = Details()
    d.rent = (_amount_after(r"(?:m[åa]nedlig\s+)?(?:husleje|leje\b|lejepris|m[åa]nedlig\s+leje)", t)
              or _amount_after(r"pris", t))
    d.aconto = _amount_after(r"(?:aconto|a\s?conto|forbrug)", t)
    m = re.search(r"(\d{2,3})(?:[.,]\d+)?\s*(?:m2|m²|kvm|m\^2)", t, re.I)
    d.size = int(m.group(1)) if m else None
    m = (re.search(r"(\d(?:[.,]5)?)\s*(?:-\s*)?(?:v[æa]r(?:else|\.)|rum\b|room)", t, re.I)
         or re.search(r"v[æa]relser\D{0,15}(\d)", t, re.I))
    d.rooms = float(m.group(1).replace(",", ".")) if m else None
    m = re.search(r"\b(8\d{3})\s+(?:Aarhus|Århus|Risskov|Viby|Højbjerg|Brabrand|Åbyhøj)", t, re.I)
    d.postcode = m.group(1) if m else None
    if not d.postcode:
        if re.search(r"Aarhus\s*C\b|Århus\s*C\b", t):
            d.postcode = "8000"
        elif re.search(r"Aarhus\s*N\b|Århus\s*N\b", t):
            d.postcode = "8200"
    if re.search(r"ubegr[æa]nset|ubestemt|tidsubegr[æa]nset", t, re.I):
        d.unlimited = True
    m = re.search(r"tidsbegr[æa]ns\w*[^.\n]{0,60}?(\d{1,2})\s*(?:m[åa]ned|mdr)", t, re.I)
    if m:
        d.unlimited, d.limited_months = False, int(m.group(1))
    elif d.unlimited is None and re.search(r"tidsbegr[æa]nset", t, re.I):
        d.unlimited = False
    d.dishwasher = bool(re.search(r"opvaskemaskine", t, re.I)) and not re.search(r"(ingen|uden)\s+opvaskemaskine", t, re.I)
    d.washer = bool(re.search(r"(?<!op)vaskemaskine|vask/t[øo]r|vaske-?/?t[øo]rre", t, re.I) and
                    not re.search(r"(f[æa]lles\s+vaskeri|vaskekælder)", t, re.I))
    return d
