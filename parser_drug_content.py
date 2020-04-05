import requests
from bs4 import BeautifulSoup
import json
from parser_links_gatherer import write_file
import asyncio
import aiohttp


links_list = [
    "/mtm/abacavir.html",
    "/mtm/abacavir-dolutegravir-and-lamivudine.html",
    "/mtm/abacavir-and-lamivudine.html",
    "/pro/abacavir-and-lamivudine-tablets.html",
    "/mtm/abacavir-lamivudine-and-zidovudine.html",
    "/pro/abacavir-lamivudine-and-zidovudine-tablets.html",
    "/cdi/abacavir-oral-solution.html",
    "/monograph/abacavir-sulfate.html",
    "/pro/abacavir-sulfate-tablets.html",
    "/cdi/abacavir-tablets.html",
    "/mtm/abaloparatide.html",
]

unused_blocks = {
    'div': [
        {'class':'pronounce-title'},
        {'class':'navNext'},
        {'class':'more-resources'}
    ],
    'ul': [
        {'class':'nav-tabs'}
    ],
    'p': [
        {'class':'ddc-reviewed-by'}
    ]
}
soups = []

def clean_page(page):
    '''Чистим ненужные блоки'''
    for key, value in unused_blocks.items():
        for val in value:
            try:
                page.find(key, attrs=val).decompose()
            except:
                print('Блок отсутствует')

def drug_content(soup):
    '''Возвращает готовый текст в html'''
    page = soup.find('div', attrs={'class':'contentBox'})#.get_text()
    name = page.find('div', attrs={'class':'pronounce-title'}).h1.text
    clean_page(page)
    all_links = page.find_all('a')
    article = BeautifulSoup('', 'html.parser')
    for link in all_links:
        #print(f'----{link.text}----')
        article.string = link.text
        link.replace_with(article)
    return page

async def get_html(url, session):
    '''Запишем суп страницы в список супов'''
    url = 'https://www.drugs.com{}'.format(url)
    async with session.get(url) as response:
        data = await response.read()
        soups.append(BeautifulSoup(data, 'html.parser'))

async def main():
    tasks = []
    async with aiohttp.ClientSession() as session:
        for link in links_list:
            task = asyncio.create_task(get_html(link, session))
            tasks.append(task)
        await asyncio.gather(*tasks)

    '''
    soup = page_prep(url)
    drug_content(soup)
    '''
if __name__ == "__main__":
    asyncio.run(main())
    print(len(soups))
    write_file(soups.pop().prettify(), fname='testasync.txt')