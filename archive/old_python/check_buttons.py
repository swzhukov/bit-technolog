"""Проверка кнопок в РЕАЛЬНОМ браузере через Playwright."""
import asyncio
import sys
from playwright.async_api import async_playwright


async def check_buttons():
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Сборщик ошибок
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(f"PAGEERROR: {exc}"))
        page.on("console", lambda msg: page_errors.append(f"CONSOLE.{msg.type}: {msg.text}") if msg.type in ("error", "warning") else None)

        try:
            # 1) LOGIN
            await page.goto("http://localhost:8000/login")
            results.append(f"1. /login: {page.url}")
            await page.fill('input[name="username"]', "baranov")
            await page.fill('input[name="password"]', "demo")
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_url("**/", timeout=5000)
            results.append(f"2. Login → /: {page.url}")

            # 3) /products
            await page.goto("http://localhost:8000/products")
            results.append(f"3. /products: {page.url}")
            count = await page.locator('a[href*="/detail/"]').count()
            results.append(f"   Найдено {count} ссылок на детали")

            # 4) Открыть деталь 3 (Втулка)
            await page.goto("http://localhost:8000/detail/3")
            results.append(f"4. /detail/3: {page.url}")
            h1 = await page.locator('h1').first.text_content()
            results.append(f"   H1: {h1}")

            # 5) Найти кнопку "Сгенерировать ТК"
            gen_btn = page.locator('a:has-text("Сгенерировать ТК")')
            if await gen_btn.count() > 0:
                results.append(f"5. Кнопка 'Сгенерировать ТК' найдена: {await gen_btn.count()}")
            else:
                results.append("5. Кнопка 'Сгенерировать ТК' НЕ найдена")

            # 6) Сгенерировать
            await page.goto("http://localhost:8000/items/8/generate")
            btn = page.locator('button[type="submit"]')
            results.append(f"6. /items/8/generate: кнопка submit = {await btn.count()}")
            # Submit form
            await page.locator('form').first.evaluate('form => form.submit()')
            await page.wait_for_url("**/detail/8*", timeout=10000)
            results.append(f"7. После генерации: {page.url}")

            # 7) Кнопки в /detail
            for btn_text in ["Утвердить", "Перегенерировать", "Экспорт в 1С", "Подтвердить", "Аналоги"]:
                loc = page.locator(f'button:has-text("{btn_text}"), a:has-text("{btn_text}")')
                cnt = await loc.count()
                results.append(f"8. Кнопка '{btn_text}': {cnt}")

            # 8) Клик по "Перегенерировать" (проверим что fetch идёт)
            req = None
            async def handle_request(req_data):
                nonlocal req
                if "/api/tech-cards/" in req_data.url and req_data.method == "POST":
                    req = req_data.url
            page.on("request", lambda r: asyncio.create_task(handle_request(r)))
            regen_btn = page.locator('button:has-text("Перегенерировать")')
            if await regen_btn.count() > 0:
                try:
                    await regen_btn.first.click()
                    await page.wait_for_timeout(2000)
                    results.append(f"9. Клик 'Перегенерировать' → POST {req or 'НЕТ ЗАПРОСА'}")
                except Exception as e:
                    results.append(f"9. Клик 'Перегенерировать' ошибка: {e}")

            # 9) Извещения
            await page.goto("http://localhost:8000/notices")
            n = await page.locator('a[href*="/notices/"]').count()
            results.append(f"10. /notices: {n} ссылок на извещения")

            # 10) /knowledge
            await page.goto("http://localhost:8000/knowledge")
            n_et = await page.locator('table.tbl tr').count()
            results.append(f"11. /knowledge: {n_et} строк в таблице эталонов")
            syn = await page.locator('text="Синтетический"').count()
            results.append(f"    Синтетических: {syn}")

            # 11) Settings (под admin)
            await page.goto("http://localhost:8000/logout")
            await page.goto("http://localhost:8000/login")
            await page.fill('input[name="username"]', "techadmin")
            await page.fill('input[name="password"]', "demo")
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_url("**/", timeout=5000)
            await page.goto("http://localhost:8000/settings")
            s = page.url
            h2 = await page.locator('h1, h2').first.text_content() if await page.locator('h1, h2').count() > 0 else "?"
            results.append(f"12. /settings (admin): URL={s} H1/H2={h2}")

        except Exception as e:
            results.append(f"!!! ОШИБКА: {e}")

        if page_errors:
            results.append("---ОШИБКИ В КОНСОЛИ---")
            for e in page_errors[:10]:
                results.append(f"  {e}")

        await browser.close()

    return results


if __name__ == "__main__":
    results = asyncio.run(check_buttons())
    for r in results:
        print(r)
