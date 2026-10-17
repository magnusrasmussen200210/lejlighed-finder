"""Tjekker udlejernes sider, finder nye relevante lejligheder og giver besked på Telegram."""
import asyncio
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from . import telegram
from .application import render
from .areas import classify
from .parse import parse
from .sites import SITES

STATE = Path(__file__).resolve().parent.parent / "state" / "seen.json"
MAX_TOTAL = 10_000
MIN_ROOMS = 2
MIN_SIZE = 45
MIN_MONTHS = 12
SENIOR = re.compile(r"\+\s?50\s?år|50\+|55\+|60\+|seniorbolig|seniorlejlighed|over 50 år", re.I)


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"seen": {}, "chat_id": None, "errors": {}}


def save_state(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False, sort_keys=True))


def evaluate(text: str, where: str = ""):
    """Returnerer (ok, area, details, flags). `where` er annoncens adresse/kort/URL og bruges til områdebestemmelse,
    så vejnavne fra andre annoncer eller sidefoden på detaljesiden ikke forvirrer."""
    d = parse(text)
    if where:
        w = parse(where)
        d.postcode = w.postcode or d.postcode
        # kortet fra oversigten handler kun om denne bolig, så dets tal foretrækkes frem for detaljesiden,
        # der ofte også viser "lignende boliger"
        for f in ("rent", "size", "rooms"):
            if getattr(w, f) is not None:
                setattr(d, f, getattr(w, f))
        if d.aconto is None:
            d.aconto = w.aconto
    area = classify(where or text, d.postcode)
    if not area:
        return False, None, d, ["område"]
    flags = []
    if SENIOR.search(text):
        return False, area, d, ["seniorbolig"]
    if d.rooms is not None and d.rooms < MIN_ROOMS:
        return False, area, d, ["værelser"]
    if d.size is not None and d.size < MIN_SIZE:
        return False, area, d, ["størrelse"]
    if d.rent is not None and d.rent + (d.aconto or 0) > MAX_TOTAL:
        return False, area, d, ["pris"]
    if d.unlimited is False and d.limited_months and d.limited_months < MIN_MONTHS:
        return False, area, d, ["lejeperiode"]
    if d.rent is None:
        flags.append("husleje ikke fundet")
    if d.aconto is None:
        flags.append("aconto ikke fundet")
    if d.rooms is None:
        flags.append("antal værelser ikke fundet")
    if d.size is None:
        flags.append("størrelse ikke fundet")
    if d.unlimited is False:
        flags.append("tidsbegrænset" + (f" ({d.limited_months} mdr)" if d.limited_months else ", tjek længden"))
    return True, area, d, flags


def fmt_kr(n):
    return f"{n:,}".replace(",", ".") + " kr"


def message(site, url, title, area, d, flags, application):
    prio = {1: "⭐⭐⭐", 2: "⭐⭐", 3: "⭐"}[area[0]]
    lines = [f"🏠 Ny lejlighed: {area[1]} {prio}", title, ""]
    if d.rent:
        total = f" (i alt {fmt_kr(d.rent + d.aconto)})" if d.aconto else ""
        lines.append(f"Husleje: {fmt_kr(d.rent)}" + (f" + aconto {fmt_kr(d.aconto)}" if d.aconto else "") + total)
    if d.size or d.rooms:
        rooms = "?" if d.rooms is None else (int(d.rooms) if d.rooms.is_integer() else d.rooms)
        lines.append(f"Størrelse: {d.size or '?'} m², {rooms} værelser")
    yn = {True: "ja ✅", False: "nej", None: "ikke nævnt"}
    lines.append("Opvaskemaskine: " + yn[d.dishwasher])
    lines.append("Vaskemaskine: " + yn[d.washer])
    lines.append("Lejeperiode: " + ("ubegrænset ✅" if d.unlimited else "tidsbegrænset" if d.unlimited is False else "ikke nævnt"))
    if flags:
        lines.append("Tjek selv: " + ", ".join(flags))
    lines += ["", f"Udlejer: {site.name}", url, ""]
    lines.append(site.how_to_apply)
    lines += ["", "Ansøgning (kopiér):", "", application]
    return "\n".join(lines)


async def fetch_text(page, url, wait_ms):
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    await page.wait_for_timeout(wait_ms)
    return await page.inner_text("body")


async def run(dry_run=False):
    from playwright.async_api import async_playwright

    state = load_state()
    chat_id = state.get("chat_id") or (os.environ.get("TELEGRAM_CHAT_ID") and int(os.environ["TELEGRAM_CHAT_ID"]))
    if not chat_id and os.environ.get("TELEGRAM_BOT_TOKEN") and not dry_run:
        chat_id = telegram.discover_chat_id()
        if chat_id:
            state["chat_id"] = chat_id
            telegram.send(chat_id, "Hej Magnus! Lejlighed Finder er sat op og tjekker nu udlejernes sider automatisk. Jeg skriver her, når der dukker en relevant lejlighed op.")
    if not chat_id and not dry_run:
        print("Ingen Telegram chat-id endnu (mangler token, eller ingen har skrevet til botten). Kører som dry run.")
        dry_run = True

    now = datetime.now(timezone.utc).isoformat(timespec="minutes")
    slot = int(datetime.now(timezone.utc).timestamp() // 600)  # nummeret på det aktuelle 10-minutters vindue
    found = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(locale="da-DK", user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"))
        page = await ctx.new_page()
        for site in SITES:
            if slot % site.every:
                continue
            try:
                listings = await site.collect(page)
                state["errors"].pop(site.name, None)
            except Exception as e:
                traceback.print_exc()
                n = state["errors"].get(site.name, 0) + 1
                state["errors"][site.name] = n
                if n == 6 and chat_id and not dry_run:  # ca. en time i træk
                    telegram.send(chat_id, f"⚠️ Kan ikke læse {site.name} i øjeblikket ({type(e).__name__}). Jeg prøver videre.")
                continue
            print(f"{site.name}: {len(listings)} annoncer")
            for url, card in listings:
                if url in state["seen"]:
                    continue
                state["seen"][url] = now
                if site.prefilter and not site.prefilter(card):
                    continue
                try:
                    text = card if site.card_is_enough else await fetch_text(page, url, site.wait_ms)
                except Exception as e:
                    print("  kunne ikke hente", url, e)
                    del state["seen"][url]
                    continue
                where = card + " " + unquote(url).replace("-", " ")
                ok, area, d, flags = evaluate(text, where)
                if dry_run:
                    print("    TEKST:", re.sub(r"\s+", " ", text)[:3000])
                print(f"  {'MATCH' if ok else 'nej  '} {url} {flags} {d}")
                if not ok:
                    continue
                found += 1
                title = site.title(card, url)
                msg = message(site, url, title, area, d, flags, render(title, area[1], d))
                if dry_run or not chat_id:
                    print(msg)
                else:
                    telegram.send(chat_id, msg)
        await browser.close()
    if not dry_run:
        save_state(state)
    print(f"Færdig: {found} nye relevante lejligheder")


if __name__ == "__main__":
    asyncio.run(run(dry_run="--dry-run" in sys.argv))
