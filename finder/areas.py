"""Områder i prioriteret rækkefølge. Trøjborg og Frederiksbjerg genkendes på navn eller vejnavn."""

TROEJBORG_STREETS = [
    "trøjborgvej", "tordenskjoldsgade", "niels juels gade", "peder skrams gade", "cort adelers gade",
    "olaf ryes gade", "herluf trolles gade", "steen billes gade", "ivar huitfeldts gade", "iver huitfeldts gade",
    "otte ruds gade", "willemoesgade", "hjelmensgade", "kaserneboulevarden", "gøteborg allé", "kalmargade",
    "stavangergade", "bergensgade", "helsingforsgade", "riis skov", "rolf krakes vej",
    "vennelystparken",
]

FREDERIKSBJERG_STREETS = [
    "jægergårdsgade", "frederiks allé", "m.p. bruuns gade", "mp bruuns gade", "sankt pauls gade", "skt. pauls gade",
    "sankt pauls kirkeplads", "ingerslevs boulevard", "fredensgade", "valdemarsgade", "bülowsgade", "dagmarsgade",
    "kriegersvej", "carl blochs gade", "wilstersgade", "odensegade", "hans broges gade", "ole rømers gade",
    "thorvaldsensgade", "tietgensgade", "rosenkrantzgade", "heibergsgade", "oehlenschlægersgade", "dalgas avenue",
    "hallssti", "sonnesgade", "ewaldsgade",
]


def classify(text: str, postcode: str | None) -> tuple[int, str] | None:
    """Returnerer (prioritet, område) eller None hvis området ikke er relevant. 1 er bedst."""
    low = text.lower()
    if postcode in (None, "8000", "8200") and ("trøjborg" in low or any(s in low for s in TROEJBORG_STREETS)):
        return 1, "Trøjborg"
    if postcode in (None, "8000") and ("frederiksbjerg" in low or any(s in low for s in FREDERIKSBJERG_STREETS)):
        return 2, "Frederiksbjerg"
    if postcode == "8000":
        return 3, "Aarhus C"
    return None
