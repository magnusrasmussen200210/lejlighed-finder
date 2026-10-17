"""Udfyld formularer uden at sende dem, og vis hvad der står i felterne. Brug: python tools/formtest.py <site> <url> ..."""
import asyncio
import sys

from playwright.async_api import async_playwright

from finder import forms


async def main(site, urls):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await (await browser.new_context(locale="da-DK")).new_page()
        for url in urls:
            try:
                print(url, "->", await forms.FORMS[site](page, url, "TEST-ANSØGNING (sendes ikke)", submit=False))
                values = await page.evaluate("""() => [...document.querySelectorAll('form input, form textarea, form select')]
                    .filter(e => e.value && e.type !== 'hidden').map(e => `${e.name}=${e.type === 'checkbox' ? e.checked : e.value.slice(0, 40)}`)""")
                print("  ", values)
            except Exception as e:
                print(url, "FEJL", type(e).__name__, e)
        await browser.close()


asyncio.run(main(sys.argv[1], sys.argv[2:]))
