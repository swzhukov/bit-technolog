import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context()
        page = await ctx.new_page()
        await page.goto('http://217.114.7.5:8081/login')
        await page.fill('input[name="username"]', 'techadmin')
        await page.fill('input[name="password"]', 'demo')
        async with page.expect_navigation():
            await page.click('button[type="submit"]')
        cookies1 = await ctx.cookies()
        print('all cookies count:', len(cookies1), 'names:', [c['name'] for c in cookies1])
        if cookies1:
            print('first cookie domain:', cookies1[0].get('domain', 'NO DOMAIN'))
        cookies2 = await ctx.cookies('http://217.114.7.5:8081')
        print('for URL count:', len(cookies2))
        # Try POST with timeout via page.request
        try:
            resp = await page.request.post('http://217.114.7.5:8081/api/operations/32/update',
                headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
                data='{"field": "time_per_unit_min", "value": "12.5"}',
                timeout=10000)
            print('page.request.post status:', resp.status, 'text:', (await resp.text())[:200])
        except Exception as e:
            print('page.request err:', e)
        await b.close()

asyncio.run(test())
