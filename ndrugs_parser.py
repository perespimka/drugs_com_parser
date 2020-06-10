from bs4 import BeautifulSoup, element
from rxlist_collect_links import write_file
import logging
import re
import requests
from openpyxl import Workbook
import sqlite3
from itertools import islice
from time import sleep

logging.basicConfig(filename='ndrugs_log.txt', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
HEADERS = ('What is {}?', '{} indications', 'How should I use {}?', 'Uses of {} in details', '{} description',
           '{} dosage', '{} interactions', '{} side effects', '{} contraindications',
           'Active ingredient matches for {}:', 'References', 'Reviews'
)
HEADERS_DICT = {'What is ': 'WHAT IS?', ' indications': 'INDICATIONS', 'How should I use ': 'HOW SHOULD I USE?', 
                ' in details': 'USES OF IN DETAILS', ' description': 'DESCRIPTION', ' dosage': 'DOSAGE', ' interactions': 'INTERACTIONS', 
                ' side effects': 'SIDE EFFECTS', ' contraindications': 'CONTRAINDICATIONS', 'Active ingredient matches for :': 'ACTIVE INGREDIENT MATCHES', 
                'References': 'REFERENCES', 'Reviews': 'REVIEWS'
}
HEADER_VALUES = ('WHAT IS?', 'INDICATIONS', 'HOW SHOULD I USE?', 'USES OF IN DETAILS', 'DESCRIPTION', 'DOSAGE', 'INTERACTIONS', 'SIDE EFFECTS',
              'CONTRAINDICATIONS', 'ACTIVE INGREDIENT MATCHES',	'REFERENCES', 'REVIEWS'
)
TAB_HEADERS= ['Name', 'link', 'WHAT IS?', 'INDICATIONS', 'HOW SHOULD I USE?', 'USES OF IN DETAILS', 'DESCRIPTION', 'DOSAGE', 'INTERACTIONS', 'SIDE EFFECTS',
              'CONTRAINDICATIONS', 'ACTIVE INGREDIENT MATCHES',	'LIST OF SUBSTITUTES (BRAND AND GENERIC NAMES)', 'REFERENCES', 'REVIEWS', 'CR useful', 
              'CR price estimates', 'CR time for results', 'CR reported age',  'DOSAGE_2', 'SIDE EFFECTS_2', 'Pregnancy', 'Overdose', 'Actions'
]
MAIN_TAB_HEADERS= ('WHAT IS?', 'INDICATIONS', 'HOW SHOULD I USE?', 'USES OF IN DETAILS', 'DESCRIPTION', 'DOSAGE', 'INTERACTIONS', 'SIDE EFFECTS',
              'CONTRAINDICATIONS', 'ACTIVE INGREDIENT MATCHES',	'LIST OF SUBSTITUTES (BRAND AND GENERIC NAMES)', 'REFERENCES', 'REVIEWS', 'CR useful', 
              'CR price estimates', 'CR time for results', 'CR reported age', 'DOSAGE_2', 'SIDE EFFECTS_2', 'Pregnancy', 'Overdose', 'Actions'
)


def get_html(url):
    '''Вернем текст страницы '''
    proxy = {
        'https': 'http://69.64.54.93:9191'
    }
    headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
    }
    r = requests.get(url, headers=headers, proxies=proxy)
    print(r.status_code)
    print(url)
    return r.text

def header_check(tag_text):
    for key in HEADERS_DICT:
        if key in tag_text:
            return HEADERS_DICT[key]


def get_main_tab_data(content, name):
    '''
    Сбор данных с основной вкладки
    '''
    headers = [header.format(name) for header in HEADERS]
    fields_convert = dict(zip(headers, HEADER_VALUES))
    key = None
    result = {col: '' for col in MAIN_TAB_HEADERS}
    first_brd_tab = True # есть две таблицы одного класса, нам нужна первая
    for tag in content.children:
        if isinstance(tag, element.Tag):
            if tag.name == 'h2':
                key = header_check(tag.text)
                #logging.debug(tag.text)
                '''
                if tag.text in fields_convert:
                    logging.debug('imhere')
                    key = fields_convert[tag.text]
                    if key not in result: 
                        result[key] = ''
                    if tag.text == 'Reviews': # После заголовка текст идет без тегов. Парсим его
                        result[key] = tag.next_sibling
                else:
                    key = None
                '''
            elif tag.name == 'table' and tag.attrs.get('class'):
                if tag.attrs.get('class')[0] == 'brd':
                    if first_brd_tab: # Проверим, первая ли таблица brd
                        result['LIST OF SUBSTITUTES (BRAND AND GENERIC NAMES)'] = str(tag).strip()
                        first_brd_tab = False
                continue
            elif key:
                if key == 'REVIEWS':
                    if tag.name == 'div' and tag.attrs.get('class'):
                        but = tag.button
                        if but:
                            but.decompose()
                        empty = False
                        if tag.attrs.get('class')[0] == 'vote_result':
                            if 'No survey data has been collected yet' in tag.text.strip():
                                continue        
                            if tag.h4.text.endswith('time for results'):
                                result['CR time for results'] = str(tag).strip()
                            elif tag.h4.text.endswith('useful'):
                                result['CR useful'] = str(tag).strip()
                            elif tag.h4.text.endswith('price estimates'):
                                result['CR price estimates'] = str(tag).strip()
                            elif tag.h4.text.endswith('reported age'):
                                result['CR reported age'] = str(tag).strip()
                elif tag.name in ['p', 'h3', 'h4', 'h5', 'ul', 'center', 'b', 'ol'] and tag.text:
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

def get_page_data(link, session):
    '''
    Сбор данных по одному препарату
    '''
    #Обработаем главную страницу
    soup = BeautifulSoup(get_html(link + '&showfull=1', session), 'lxml')
    name = soup.h1
    name = re.search(r'^(.+) Uses', name.text).group(1)
    content = soup.find('div', attrs={'class': 'content'})
    result = get_main_tab_data(content, name)
    result['Name'] = name
    result['link'] = link
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
        yield drug_data.get(tab_header)



def to_db(drug_data):
    conn = sqlite3.connect('parser.db')
    cursor = conn.cursor()
    query = 'SELECT link FROM ndrugs WHERE link=?'
    cursor.execute(query, (drug_data['link'],))
    if cursor.fetchone():
        query = '''UPDATE ndrugs SET
                       name=?,  link=?, what_is=?, indications=?, 
                       how_should_i_use=?, uses_of_in_details=?, description=?, 
                       dosage=?, interactions=?, side_effects=?, contraindications=?, 
                       active_ingredient_matches=?,	
                       list_of_substitutes=?, references_=?, 
                       reviews=?, cr_useful=?, cr_price_estimates=?, 
                       cr_time_for_results=?, cr_reported_age=?, 
                       dosage_2=?, side_effects_2=?, pregnancy=?, overdose=?, 
                       actions=? 
                       WHERE link=?;
        '''
        TAB_HEADERS.append('link')
        cursor.execute(query, [drug_data[key] for key in TAB_HEADERS])
        TAB_HEADERS.pop()

        conn.commit()
    else:
        query = '''INSERT INTO ndrugs (
                        name, link, what_is, indications, how_should_i_use, uses_of_in_details, description, dosage, interactions, 
                        side_effects, contraindications, active_ingredient_matches, list_of_substitutes, references_, reviews, 
                        cr_useful, cr_price_estimates, cr_time_for_results, cr_reported_age, dosage_2, side_effects_2, pregnancy, overdose, actions
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
        '''
        cursor.execute(query, [drug_data[key] for key in TAB_HEADERS])
        conn.commit()

    conn.close()
    print(f'{drug_data["Name"]} added to DB')

def db_to_xlsx(field, values, fname='ndrugs_output.xlsx'):
    '''
    Записываем в xlsx, атрибуты - поле, по которому делаем отбор и последовательность значений этого поля
    '''
    query = f'SELECT * FROM ndrugs WHERE {field}=?'
    wb = Workbook()
    ws = wb.active
    ws.append(TAB_HEADERS)
    conn = sqlite3.connect('parser.db')
    cursor = conn.cursor()
    for value in values:
        cursor.execute(query, (value, ))
        ws.append(cursor.fetchone())
    wb.save(fname)
    conn.close()
    print(f'{fname} recorded')

def main():
    #link = 'https://www.ndrugs.com/?s=bendazol'
    session = requests.session()
    with open('ndrugs_com_urls_clean.txt') as f:
        links = islice(f, 51, 151)
        for link in links:
            drug_data = get_page_data(link.strip(), session)
            to_db(drug_data)
            sleep(1)


    '''
    list_of_results = []
    list_of_results.append(get_page_data(link))
    wb = Workbook()
    ws = wb.active
    ws.append(TAB_HEADERS)
    for drug_data in list_of_results:
        gen = sort_drug_values_gen(drug_data)
        ws.append(gen)
    wb.save('ndrugs_result.xlsx')
    '''



def test1():
    a = '<a name="review"></a><h2>Reviews</h2>The results of a survey conducted on ndrugs.com for Bendazol are given in detail below. The results of the survey conducted are based on the impressions and views of the website users and consumers taking Bendazol. We implore you to kindly base your medical condition or therapeutic choices on the result or test conducted by a physician or licensed medical practitioners.<h3>User reports</h3>'
    soup = BeautifulSoup(a, 'lxml')
    b = soup.h2.next_sibling
    print(b)

if __name__ == "__main__":
    #main()
    #db_to_xlsx('rowid', range(2,31))
    #test1()
    get_page_data('https://www.ndrugs.com/?s=%26alpha;-bisabolol/lactic%20acid/miglyol')
