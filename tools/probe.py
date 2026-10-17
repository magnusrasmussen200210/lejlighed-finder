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
            json_calls.append((resp.request.method, resp.url, len(body), body[:3000]))

    page.on("response", on_response)
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
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
    forms = await page.eval_on_selector_all("form", """els => els.map(f => [f.action, f.method, Array.from(f.elements).map(e => {
        const lab = (e.labels && e.labels[0] && e.labels[0].innerText) || e.placeholder || e.getAttribute('aria-label') || '';
        const opts = e.tagName === 'SELECT' ? '{' + Array.from(e.options).slice(0, 8).map(o => o.value).join('/') + '}' : '';
        return `${e.tagName.toLowerCase()}:${e.type}:${e.name||e.id}${e.required ? '*' : ''}[${lab.trim().slice(0, 40)}]${opts}`;
    }).join(' | ')])""")
    for f in forms:
        print("FORM", f)
    iframes = [f.url for f in page.frames if f.url and f.url != page.url]
    if iframes:
        print("IFRAMES", iframes[:10])
    for m, u, n, b in json_calls:
        print("JSON", m, u, n, b.replace("\n", " ")[:3000])
    text = await page.inner_text("body")
    print("TEXT", re.sub(r"\s+", " ", text)[:4000])
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
