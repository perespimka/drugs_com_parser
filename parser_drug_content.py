import requests
from bs4 import BeautifulSoup
import json
from parser_links_gatherer import get_html, write_file


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

def drug_content(soup):
    page = soup.find('div', attrs={'class':'contentBox'})#.get_text()
    name = page.find('div', attrs={'class':'pronounce-title'}).h1.text

    #Чистим ненужные блоки

    for key, value in unused_blocks.items():
        for val in value:
            try:
                page.find(key, attrs=val).decompose()
            except:
                print('Блок ')
    '''
    page.find('div', attrs={'class':'pronounce-title'}).decompose()
    page.find('ul', attrs={'class':'nav-tabs'}).decompose()
    page.find('p', attrs={'class':'ddc-reviewed-by'}).decompose()
    page.find('div', attrs={'class':'navNext'}).decompose()
    page.find('div', attrs={'class':'more-resources'}).decompose()
    '''

    all_links = page.find_all('a')
    article = BeautifulSoup('', 'html.parser')
    
    for link in all_links:
        #print(f'----{link.text}----')
        article.string = link.text
        link.replace_with(article)


    write_file(str(page), fname='page_example.html')


def page_prep(links_list):
    url = 'https://www.drugs.com{}'.format(links_list[0])
    return BeautifulSoup(get_html(url), 'html.parser')

def main():
    soup = page_prep(links_list)
    drug_content(soup)

if __name__ == "__main__":
    main()