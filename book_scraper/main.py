import asyncio
import json
from urllib.parse import urljoin
from pathlib import Path
from playwright.async_api import async_playwright
from utils.helpers import clean_price


BASE_URL = "https://books.toscrape.com/"
SIMULTANEAS_WINDOWS = 5 

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "database"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "maiores_precos_por_categoria.json"



async def most_expensive_book_on_page(page):
    await page.wait_for_selector("article.product_pod")

    prices = page.locator("article.product_pod .product_price .price_color")
    titles = page.locator("article.product_pod h3 a")  

    n = await prices.count()

    biggest_price = 0.0
    most_expensive_book_tile = None
    most_expensive_book_link = None

    for i in range(n):
        price_txt = await prices.nth(i).inner_text()
        price = clean_price(price_txt)

        if price > biggest_price:
            biggest_price = price
            most_expensive_book_tile = await titles.nth(i).get_attribute("title")
            href = await titles.nth(i).get_attribute("href")
            most_expensive_book_link = urljoin(page.url, href)

    return biggest_price, most_expensive_book_tile, most_expensive_book_link


async def extrair_maior_preco_categoria(context, url, sem):
    async with sem:
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")

            # nome da categoria (h1 da página)
            await page.wait_for_selector(".page-header h1")
            nome_categoria = (await page.locator(".page-header h1").inner_text()).strip()

            biggest_price = 0.0
            most_expensive_book_title = None
            most_expensive_book_link = None

            while True:
                page_price, page_name, page_link = await most_expensive_book_on_page(page)

                if page_price > biggest_price:
                    biggest_price = page_price
                    most_expensive_book_title = page_name
                    most_expensive_book_link = page_link

                next_btn = page.locator("li.next > a")
                if await next_btn.count() == 0:
                    break

                href = await next_btn.get_attribute("href")
                await page.goto(urljoin(page.url, href), wait_until="domcontentloaded")

            return {
                "nome_categoria": nome_categoria,
                "maior_preco": biggest_price,
                "livro_mais_caro": most_expensive_book_title,
                "url_livro": most_expensive_book_link,
                "categoria_url": url,
            }

        except Exception as e:
            print(f"Erro ao processar {url}: {e}")
            return None
        finally:
            await page.close()


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # links das categorias (exclui "Books" automaticamente)
        main_page = await context.new_page()
        await main_page.goto(BASE_URL, wait_until="domcontentloaded")
        await main_page.wait_for_selector("ul.nav.nav-list")

        categories = main_page.locator("ul.nav.nav-list > li > ul > li > a")
        count = await categories.count()

        urls = []
        for i in range(count):
            href = await categories.nth(i).get_attribute("href")
            urls.append(urljoin(BASE_URL, href))

        await main_page.close()

        sem = asyncio.Semaphore(SIMULTANEAS_WINDOWS)
        tasks = [extrair_maior_preco_categoria(context, url, sem) for url in urls]

        print(f"Iniciando extração de {len(urls)} categorias...")
        resultados = await asyncio.gather(*tasks)

        dados_finais = [r for r in resultados if r is not None]

        print("CWD (onde o Python está rodando):", Path.cwd())
        print("OUTPUT_FILE:", OUTPUT_FILE)
        print("OUTPUT_FILE absoluto:", OUTPUT_FILE.resolve())
        print("Qtd resultados:", len(resultados))
        print("Qtd dados_finais:", len(dados_finais))


        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)

        print(f"Sucesso! {len(dados_finais)} categorias salvas em {OUTPUT_FILE}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
