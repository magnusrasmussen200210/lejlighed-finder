"""Tilpas master-ansøgningen til en konkret bolig."""
import os
import re
from pathlib import Path

AREA_SENTENCES = {
    "Trøjborg": "Trøjborg har længe været vores klare førstevalg. Vi holder af den rolige stemning, nærheden til Riis Skov og vandet og den korte vej til universitetet.",
    "Frederiksbjerg": "Frederiksbjerg er et af vores yndlingsområder i byen. Vi holder af stemningen omkring Jægergårdsgade og den korte vej til både centrum og Marselisborgskovene.",
}


def _template() -> str:
    tpl = os.environ.get("ANSOEGNING")
    if tpl:
        return tpl
    return Path(__file__).with_name("ansoegning_eksempel.txt").read_text(encoding="utf-8")


def render(address: str, area: str, details) -> str:
    extras = []
    if details.dishwasher:
        extras.append("opvaskemaskine")
    if details.washer:
        extras.append("vaskemaskine")
    if extras:
        bolig = f"Det betyder meget for os, at lejligheden har {' og '.join(extras)}, og den virker som et rigtig godt sted for os at starte vores fælles hjem."
    else:
        bolig = "Lejligheden virker som et rigtig godt sted for os at starte vores fælles hjem."
    text = (_template()
            .replace("{adresse}", address)
            .replace("{omraade_saetning}", AREA_SENTENCES.get(area, ""))
            .replace("{bolig_saetning}", bolig)
            .replace("{telefon}", os.environ.get("KONTAKT_TELEFON", "[telefon]"))
            .replace("{email}", os.environ.get("KONTAKT_EMAIL", "[email]")))
    # Sikkerhedsnet: en pladsholder der ikke blev udfyldt (fx stavet forkert) må aldrig nå en udlejer
    text = re.sub(r"[^\n]*\{[^{}\n]*\}[^\n]*\n?", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
