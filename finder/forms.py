"""Udfyld og send udlejernes egne ansøgningsformularer med Playwright."""
import os


def contact():
    return {
        "name": os.environ.get("KONTAKT_NAVN", "Magnus Rasmussen"),
        "phone": os.environ.get("KONTAKT_TELEFON", ""),
        "email": os.environ.get("KONTAKT_EMAIL", ""),
    }


def ready() -> bool:
    c = contact()
    return bool(c["phone"] and c["email"] and os.environ.get("ANSOEGNING"))


async def _accept_cookies(page):
    for label in ("Accepter alle", "ACCEPTER ALLE", "Acceptér alle", "Tillad alle", "OK"):
        try:
            await page.get_by_role("button", name=label, exact=True).first.click(timeout=1500)
            return
        except Exception:
            pass


async def heimstaden(page, url, text, submit):
    c = contact()
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await _accept_cookies(page)
    form = page.locator("form.wpcf7-form").first
    await form.locator("[name=your-name]").fill(c["name"])
    await form.locator("[name=your-phone]").fill(c["phone"])
    await form.locator("[name=your-email]").fill(c["email"])
    await form.locator("[name=adults]").fill("2")
    await form.locator("[name=kids]").fill("0")
    await form.locator("[name=comments]").fill(text)
    # afkrydsningsfeltet er skjult bag en stylet label, så det sættes direkte
    await form.locator("[name=terms]").evaluate(
        "e => { e.checked = true; e.dispatchEvent(new Event('change', {bubbles: true})); }")
    if not submit:
        return "udfyldt (ikke sendt)"
    await form.locator("[type=submit]").click()
    await page.wait_for_selector("form.wpcf7-form.sent, form.wpcf7-form.invalid, form.wpcf7-form.failed", timeout=20000)
    if await page.locator("form.wpcf7-form.sent").count():
        return "sendt"
    raise RuntimeError(await form.locator(".wpcf7-response-output").inner_text())


async def ae_ejendom(page, url, text, submit):
    c = contact()
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await _accept_cookies(page)
    try:
        await page.get_by_text("Jeg er interesseret", exact=True).first.click(timeout=5000)
    except Exception:
        pass
    form = page.locator("form[action*='website-interests']").first
    await form.locator("[name=name]").fill(c["name"])
    await form.locator("[name=email]").fill(c["email"])
    await form.locator("[name=phone]").fill(c["phone"])
    await form.locator("[name=note]").fill(text)
    await form.locator("[name=privacy]").check(force=True)
    # feltet "website" er en fælde for spam-robotter og skal forblive tomt
    if not submit:
        return "udfyldt (ikke sendt)"
    before = page.url
    await form.locator("[type=submit]").click()
    await page.wait_for_load_state("networkidle", timeout=20000)
    body = (await page.inner_text("body")).lower()
    if "tak" in body or page.url != before:
        return "sendt"
    raise RuntimeError("ingen kvittering efter afsendelse")


FORMS = {"Heimstaden": heimstaden, "AE Ejendom": ae_ejendom}
