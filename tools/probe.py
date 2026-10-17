"""Debug-værktøj: henter udlejer-sider og logger links og JSON-kald, så adaptere kan skrives."""
import asyncio
import re
import sys
from urllib.parse import urljoin

from playwright.async_api import async_playwright

KEYWORDS = re.compile(r"ledig|lejebolig|lejem[aå]a?l|find-?bolig|bolig|lejlighed|apartment|rent|udlej", re.I)


async def probe(browser, url):
    print(f"\n===== {url}")
    page = await browser.new_page(locale="da-DK")
    json_calls = []

    async def on_response(resp):
        ct = resp.headers.get("content-type", "")
        if "json" in ct and resp.request.resource_type in ("xhr", "fetch"):
            try:
                body = await resp.text()
            except Exception:
                body = ""
            json_calls.append((resp.request.method, resp.url, len(body), body[:600]))

    page.on("response", on_response)
    try:
        resp = await page.goto(url, wait_until="networkidle", timeout=45000)
        print("status", resp.status if resp else None, "final", page.url)
    except Exception as e:
        print("GOTO ERROR", e)
    await page.wait_for_timeout(2500)
    links = await page.eval_on_selector_all("a[href]", "els => els.map(e => [e.href, (e.innerText||'').trim().slice(0,80)])")
    seen = set()
    for href, text in links:
        if href in seen or not KEYWORDS.search(href + " " + text):
            continue
        seen.add(href)
        print("LINK", href, "|", text.replace("\n", " "))
    forms = await page.eval_on_selector_all("form", "els => els.map(f => [f.action, f.method, Array.from(f.elements).map(e => e.name||e.id||e.type).join(',')])")
    for f in forms:
        print("FORM", f)
    for m, u, n, b in json_calls:
        print("JSON", m, u, n, b.replace("\n", " ")[:600])
    text = await page.inner_text("body")
    print("TEXT", re.sub(r"\s+", " ", text)[:1500])
    await page.close()


async def main(urls):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for u in urls:
            try:
                await probe(browser, u)
            except Exception as e:
                print("ERROR", u, e)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
