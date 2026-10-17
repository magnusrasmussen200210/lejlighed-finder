"""Udlejere der tjekkes. Hver side beskrives af hvor annoncerne står, og hvordan et link til en annonce ser ud."""
import re
from dataclasses import dataclass
from urllib.parse import unquote, urljoin

RELEVANT = re.compile(r"aarhus[-\s]?c\b|aarhus[-\s]?n\b|århus[-\s]?[cn]\b|\b8000\b|\b8200\b|trøjborg|troejborg|frederiksbjerg", re.I)
OTHER_CITY = re.compile(r"aalborg|vejle|københavn|kobenhavn|frederiksberg|valby|brøndby|rødovre|esbjerg|kolding|odense|"
                        r"svendborg|fredericia|horsens|køge|hillerød|risskov|viby|højbjerg|brabrand|aarhus\s?v\b|tilst|"
                        r"lystrup|skejby|randers|silkeborg|roskilde|glostrup|ballerup", re.I)
POSTCODE = re.compile(r"\b([1-9]\d{3})\b(?=[\s,-]+[a-zæøå])", re.I)


def default_prefilter(card: str) -> bool:
    """Spring annoncer over, hvis kortet tydeligt ligger uden for Aarhus C/N."""
    if RELEVANT.search(card):
        return True
    return not (POSTCODE.search(card) or OTHER_CITY.search(card))


def first_line_title(text: str, url: str) -> str:
    m = re.search(r"[A-ZÆØÅ][\wæøåÆØÅé.' -]+?\s\d+[A-Za-z]?(?:,\s*[\w. ]+?)?,?\s+8[02]00\s+Aarhus\s+[CN]", text)
    if m:
        return re.sub(r"\s+", " ", m.group(0))
    slug = unquote(url.rstrip("/").split("/")[-1])
    return slug.replace("-", " ").strip() or url


@dataclass
class Site:
    name: str
    list_urls: list[str]
    link_re: str
    how_to_apply: str
    wait_ms: int = 2000
    card_is_enough: bool = False
    prefilter: object = default_prefilter
    every: int = 1  # tjek kun hver n'te kørsel (for sider der blokerer hyppige besøg)

    def title(self, text, url):
        return first_line_title(text, url)

    async def collect(self, page):
        out, seen = [], set()
        rx = re.compile(self.link_re)
        for list_url in self.list_urls:
            await page.goto(list_url, wait_until="domcontentloaded", timeout=45000)
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            await page.wait_for_timeout(self.wait_ms)
            links = await page.eval_on_selector_all(
                "a[href]",
                """els => els.map(e => {
                    const card = e.closest('article, li, .card, [class*=card], [class*=item], [class*=listing]') || e;
                    return [e.href, (card.innerText || e.innerText || '').trim()];
                })""")
            for href, card in links:
                href = urljoin(list_url, href).split("#")[0]
                if href in seen or not rx.search(href):
                    continue
                seen.add(href)
                out.append((href, re.sub(r"\s+", " ", card) + " " + unquote(href)))
        return out


SITES = [
    Site(
        name="Taurus",
        list_urls=["https://www.taurus.dk/boligudlejning/ledige-lejemal/"],
        link_re=r"taurus\.dk/boligudlejning/lejebolig\?id=\d+",
        how_to_apply="Søg via linket (Taurus' egen side).",
    ),
    Site(
        name="Laros",
        list_urls=["https://www.laros.dk/ledige-lejemal"],
        link_re=r"laros\.dk/ledige-lejemal/[a-z0-9-]+-\d+$",
        how_to_apply="Søg via linket (Laros' egen side).",
    ),
    Site(
        name="Heimstaden",
        list_urls=["https://www.heimstaden.dk/ledige-lejeboliger/?city=Aarhus"],
        link_re=r"heimstaden\.dk/lejebolig/[a-z0-9-]+/?$",
        how_to_apply="Søg via linket. Heimstaden kræver en gratis profil.",
    ),
    Site(
        name="Vidar Ejendomme",
        list_urls=["https://vidarejendomme.dk/find-bolig/by-aarhus/"],
        link_re=r"vidarejendomme\.dk/lejebolig/[a-z0-9-]+/?$",
        how_to_apply="Søg via formularen på linket.",
    ),
    Site(
        name="Go'Bolig",
        list_urls=["https://gobolig.dk/soeg-lejebolig/#filter[city=8000:8200]"],
        link_re=r"gobolig\.dk/midtjylland/aarhus-[cn]/",
        how_to_apply="Søg via linket. Go'Bolig kræver en gratis profil.",
        wait_ms=4000,
    ),
    Site(
        name="Phoenix Home",
        list_urls=["https://www.phoenixhome.dk/find-bolig/"],
        link_re=r"phoenixhome\.dk/find-bolig/[^/?#]+/?$",
        how_to_apply="Søg via linket.",
    ),
    Site(
        name="Findbolig.nu",
        list_urls=["https://www.findbolig.nu/da-dk/find?Commune=Aarhus&Rent=0%2C10000&Rooms=2%2C10&Area=45%2C500"],
        link_re=r"findbolig\.nu/da-dk/residence/\d+",
        how_to_apply="Søg via linket. Findbolig kræver en gratis profil.",
        wait_ms=4000,
    ),
    Site(
        name="AE Ejendom",
        list_urls=["https://aeejendom.dk/ledige-lejemal?q=Aarhus%20C", "https://aeejendom.dk/ledige-lejemal?q=Aarhus%20N"],
        link_re=r"aeejendom\.dk/lejemaal/[a-z0-9-]+$",
        how_to_apply="Søg via linket.",
    ),
    Site(
        name="UngdomsboligAarhus",
        list_urls=["https://ungdomsboligaarhus.dk/alle-boliger-uden-ventetid"],
        link_re=r"ungdomsboligaarhus\.dk/lejemaal/\d+/",
        how_to_apply="Kræver en ansøgning hos UngdomsboligAarhus (begge skal være studerende).",
    ),
]
