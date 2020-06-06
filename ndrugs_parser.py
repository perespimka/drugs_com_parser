from bs4 import BeautifulSoup, element
from rxlist_collect_links import write_file
import logging
import re
import requests
from openpyxl import Workbook


logging.basicConfig(filename='ndrugs_log.txt', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
HEADERS = ('What is {}?', '{} indications', 'How should I use {}?', 'Uses of {} in details', '{} description',
           '{} dosage', '{} interactions', '{} side effects', '{} contraindications',
           'Active ingredient matches for {}:', 'References', 'Reviews'
)
HEADER_VALUES = ('WHAT IS?', 'INDICATIONS', 'HOW SHOULD I USE?', 'USES OF IN DETAILS', 'DESCRIPTION', 'DOSAGE', 'INTERACTIONS', 'SIDE EFFECTS',
              'CONTRAINDICATIONS', 'ACTIVE INGREDIENT MATCHES',	'REFERENCES', 'REVIEWS'
)
TAB_HEADERS= ('Name', 'WHAT IS?', 'INDICATIONS', 'HOW SHOULD I USE?', 'USES OF IN DETAILS', 'DESCRIPTION', 'DOSAGE', 'INTERACTIONS', 'SIDE EFFECTS',
              'CONTRAINDICATIONS', 'ACTIVE INGREDIENT MATCHES',	'LIST OF  SUBSTITUTES (BRAND AND GENERIC NAMES)', 'REFERENCES', 'REVIEWS', 'CR useful', 
              'CR price estimates', 'CR time for results', 'CR reported age'#, 'USES_2', 'DOSAGE_2', 'SIDE EFFECTS_2', 'Pregnancy', 'Overdose', 'Actions'
)
def get_html(url):
    '''Вернем текст страницы '''
    headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
    }
    r = requests.get(url, headers=headers)
    print(r.status_code)
    print(url)
    return r.text

def get_main_tab_data(content, name):
    '''
    Сбор данных с основной вкладки
    '''
    headers = [header.format(name) for header in HEADERS]
    fields_convert = dict(zip(headers, HEADER_VALUES))
    key = None
    result = {}
    for tag in content.children:
        if isinstance(tag, element.Tag):
            if tag.name == 'h2':
                if tag.text in fields_convert:
                    key = fields_convert[tag.text]
                    if key not in result: 
                        result[key] = ''
                    if tag.text == 'Reviews': # После заголовка текст идет без тегов. Парсим его
                        result[key] = tag.next_sibling
                else:
                    key = None
            elif tag.name == 'table' and tag.attrs.get('class'):
                if tag.attrs.get('class')[0] == 'brd':
                    result['LIST OF  SUBSTITUTES (BRAND AND GENERIC NAMES)'] = str(tag).strip()
                continue
            elif key:
                if key == 'REVIEWS':
                    if tag.name == 'div' and tag.attrs.get('class'):
                        but = tag.button
                        if but:
                            but.decompose()
                        if tag.attrs.get('class')[0] == 'vote_result':
                            if tag.h4.text.endswith('time for results'):
                                result['CR time for results'] = str(tag).strip()
                            elif tag.h4.text.endswith('useful'):
                                result['CR useful'] = str(tag).strip()
                            elif tag.h4.text.endswith('price estimates'):
                                result['CR price estimates'] = str(tag).strip()
                            elif tag.h4.text.endswith('reported age'):
                                result['CR reported age'] = str(tag).strip()
                elif tag.name in ['p', 'h3', 'h4', 'h5', 'ul', 'center', 'b', 'ol']:
                    result[key] += str(tag).strip()
                elif tag.name == 'div' and tag.attrs.get('class'): #обрабатываем блок i
                    if tag.attrs.get('class')[0] == 'item':
                        result[key] += str(tag.text).strip()
    return result

def get_other_tabs(link, key):
    soup = BeautifulSoup(get_html(link), 'lxml')
    content = soup.find('div', attrs={'class': 'content'})
    check = False
    review = False
    result = {key: ''}
    for tag in content.children:
        if isinstance(tag, element.Tag):
            if tag.name == 'h2':
                check = True
                if tag.text == 'Reviews':
                    review = True
            elif check:
                if tag.name in ['p', 'h4', 'h5', 'ul', 'center', 'b', 'ol']:
                    result[key] += str(tag).strip()

def get_page_data(link):
    '''
    Сбор данных по одному препарату
    '''
    #Обработаем главную страницу
    soup = BeautifulSoup(get_html(link), 'lxml')
    name = soup.h1
    name = re.search(r'^(.+) Uses', name.text).group(1)
    content = soup.find('div', attrs={'class': 'content'})
    result = get_main_tab_data(content, name)
    result['Name'] = name
    '''
    # и все остальные страницы
    inner_links = {'&t=dosage': 'DOSAGE_2', '&t=side effects': 'SIDE EFFECTS_2', '&t=pregnancy': 'Pregnancy', 
                   '&t=overdose': 'Overdose', '&t=actions': 'Actions'
    }

    for i_link_key in inner_links:
        i_link = link + i_link_key
        another_tab = get_other_tabs(i_link, inner_links[i_link_key])
    '''
    write_file(result, 'result.json')      
    return result

def sort_drug_values_gen(drug_data):
    for tab_header in TAB_HEADERS:
        yield drug_data[tab_header]

def main():
    link = 'https://www.ndrugs.com/?s=bendazol'
    result = []
    result.append(get_page_data(link))
    wb = Workbook()
    ws = wb.active
    ws.append(TAB_HEADERS)
    for drug_data in result:
        gen = sort_drug_values_gen(drug_data)
        ws.append(gen)
    wb.save('ndrugs_result.xlsx')




def test1():
    a = '<a name="review"></a><h2>Reviews</h2>The results of a survey conducted on ndrugs.com for Bendazol are given in detail below. The results of the survey conducted are based on the impressions and views of the website users and consumers taking Bendazol. We implore you to kindly base your medical condition or therapeutic choices on the result or test conducted by a physician or licensed medical practitioners.<h3>User reports</h3>'
    soup = BeautifulSoup(a, 'lxml')
    b = soup.h2.next_sibling
    print(b)

if __name__ == "__main__":
    main()
    #test1()

