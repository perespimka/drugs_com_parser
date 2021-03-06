from bs4 import BeautifulSoup, element
from rxlist_collect_links import write_file
import logging
import re
import requests
from openpyxl import Workbook
import sqlite3
from itertools import islice
from time import sleep
from random import randint


 


logging.basicConfig(filename='ndrugs_log.txt', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
HEADERS = ('What is {}?', '{} indications', 'How should I use {}?', 'Uses of {} in details', '{} description',
           '{} dosage', '{} interactions', '{} side effects', '{} contraindications',
           'Active ingredient matches for {}:', 'References', 'Reviews'
)
HEADERS_DICT = {'What is ': 'WHAT IS?', ' indications': 'INDICATIONS', 'How should I use ': 'HOW SHOULD I USE?', 
                ' in details': 'USES OF IN DETAILS', ' description': 'DESCRIPTION', ' dosage': 'DOSAGE', ' interactions': 'INTERACTIONS', 
                ' side effects': 'SIDE EFFECTS', ' contraindications': 'CONTRAINDICATIONS', 'Active ingredient matches ': 'ACTIVE INGREDIENT MATCHES', 
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


PROXY2 = '161.35.114.60:8080'
PROXY3 = '45.76.137.71:8080'
PROXY4 = '64.225.77.173:8080'
PROXY5 = '198.98.54.241:8080'
PROXY6 = '80.187.140.26:8080'
PROXY7 = '178.63.41.235:9999'
PROXY8 = '51.158.172.165:8811'
PROXY9 = '52.179.18.244	8080'


def proxy_gen(start):
    with open ('proxz.txt') as f:
        for line in islice(f, start, None):
            for i in range(20):
                switch = yield line.strip(), i
                if switch == 'switch':
                    break
            
gen = proxy_gen(68)

def get_html(url, session):
    '''Вернем текст страницы '''

    proxy, count = next(gen)
    proxies = {
        'http': 'http://' + proxy,
        'https': 'http://' + proxy
    }
    headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
    }
    try:
        r = session.get(url, headers=headers, proxies=proxies)#, allow_redirects=True)
    except:
        print(f'Ошибка. Переключаем прокси {proxy}, использованную {count} раз')
        logging.info(f'Ошибка. Переключаем прокси {proxy}, использованную {count} раз')
        gen.send('switch')
        print('Ждем 10 секунд...')
        sleep(10)
        return get_html(url, session)
    if r.status_code in (503, 500, 502):
        print('Cервер пятисотит. Ждем минуту...')
        logging.info('Cервер пятисотит. Ждем минуту...')
        sleep(60)
        r = session.get(url, headers=headers, proxies=proxies)
    print()
    print(r.status_code)
    print(url)
    logging.info('******'*3)
    logging.info(r.status_code)
    logging.info(url)
    logging.info(f'PROXY: {proxy}, used {count} times')
    result = r.text
    if r.status_code in (403, 407, 404, 400):
        print(f'Ошибка {r.status_code}. Переключаем прокси {proxy}')
        logging.info(f'Ошибка {r.status_code}. Переключаем прокси {proxy}')
        sleep(5)
        gen.send('switch')
        return get_html(url, session)
    

    return result

def header_check(tag_text):
    '''
    Проверка h2 заголовков, совпадают ли они с разделами, которые нам нужно спарсить
    '''
    for key in HEADERS_DICT:
        if key in tag_text:
            return HEADERS_DICT[key]

def link_to_text(a):
    '''Меняет ссылку на текст'''
    sub = BeautifulSoup(a.text, 'html.parser')
    a.replace_with(sub)

def link_cleaner(tag):
    '''Ссылки превращаем в обычный текст, также ссылки на разделы сайта убираем'''
    links = tag.find_all('a')
    for link in links:
        link_to_text(link)

def get_main_tab_data(content, name):
    '''
    Сбор данных с основной вкладки
    '''
    
    key = None
    result = {col: '' for col in MAIN_TAB_HEADERS}
    first_brd_tab = True # есть две таблицы одного класса, нам нужна первая
    for tag in content.children:
        if isinstance(tag, element.Tag):
            if tag.name == 'h2':
                key = header_check(tag.text)
            elif tag.name == 'table' and tag.attrs.get('class'):
                if tag.attrs.get('class')[0] == 'brd':
                    if first_brd_tab: # Проверим, первая ли таблица brd
                        link_cleaner(tag)
                        result['LIST OF SUBSTITUTES (BRAND AND GENERIC NAMES)'] = str(tag).strip()
                        first_brd_tab = False
                continue
            elif key:
                if key == 'REVIEWS':
                    if tag.name == 'div' and tag.attrs.get('class'):
                        but = tag.button
                        if but:
                            but.decompose()
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

    result = {key: ''}
    for tag in content.children:
        if isinstance(tag, element.Tag):
            if tag.name == 'h2':
                check = True
                if tag.text == 'Reviews':
                    pass
            elif check:
                if tag.name in ['p', 'h4', 'h5', 'ul', 'center', 'b', 'ol']:
                    result[key] += str(tag).strip()
"""
def create_selenium_driver():
    opts = Options()
    opts.headless = True
    assert opts.headless
    caps = webdriver.DesiredCapabilities.FIREFOX
    caps['marionette'] = True    
    caps['proxy'] = {
    "proxyType": "MANUAL",
    "httpProxy": PROXY,
    "ftpProxy": PROXY,
    "sslProxy": PROXY
    }
    
    driver = webdriver.Firefox(options=opts, capabilities=caps)
    return driver

def get_soup_via_selenium(link, driver):
    '''
    Создаем суп по ссылке. Драйвер не закрываем, дабы сохранить сессию
    '''

    driver.get(link)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    logging.debug(soup.prettify())

    return soup

"""



def get_page_data(link, session):
    '''
    Сбор данных по одному препарату
    '''
    #Обработаем главную страницу
    soup = BeautifulSoup(get_html(link + '&showfull=1', session), 'lxml')
    #logging.debug(soup.prettify())
    name = soup.h1
    try:
        name = re.search(r'^(.+) Uses', name.text).group(1)
    except:
        return None
    content = soup.find('div', attrs={'class': 'content'})
    result = get_main_tab_data(content, name)
    result['Name'] = name
    result['link'] = link
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

def db_to_xlsx(field=None, values=None, all=True, fname='ndrugs_output.xlsx'):
    '''
    Записываем в xlsx, атрибуты - поле, по которому делаем отбор и последовательность значений этого поля
    '''
    wb = Workbook()
    ws = wb.active
    ws.append(TAB_HEADERS)
    conn = sqlite3.connect('parser.db')
    cursor = conn.cursor()
    if all:
        query = f'SELECT * FROM ndrugs'
        cursor.execute(query)
        for rec in cursor.fetchall():
            ws.append(rec)
    else:
        query = f'SELECT * FROM ndrugs WHERE {field}=?'
        for value in values:
            cursor.execute(query, (value, ))
            ws.append(cursor.fetchone())
    wb.save(fname)
    conn.close()
    print(f'{fname} recorded')

def main():
    session = requests.Session()
    with open('ndrugs_com_urls_clean.txt') as f:
        links = islice(f, 708, 1000)
        for link in links:
            link = link.replace('https', 'http')
            drug_data = get_page_data(link.strip(), session)
            if drug_data:
                to_db(drug_data)
            else:
                logging.warning(f'Ссылка {link} не спаршена')
            sleep(randint(1,5))


def test1():
    a = '<a name="review"></a><h2>Reviews</h2>The results of a survey conducted on ndrugs.com for Bendazol are given in detail below. The results of the survey conducted are based on the impressions and views of the website users and consumers taking Bendazol. We implore you to kindly base your medical condition or therapeutic choices on the result or test conducted by a physician or licensed medical practitioners.<h3>User reports</h3>'
    soup = BeautifulSoup(a, 'lxml')
    b = soup.h2.next_sibling
    print(b)

def test2(link):
    session = requests.Session()

    get_page_data(link , session)
def test3():
    link = 'http://yandex.ru'
    #soup = get_soup_via_selenium(link,driver)


if __name__ == "__main__":
    main()
    #db_to_xlsx()
    
    #test2('http://www.ndrugs.com/?s=%C4%B0esef')
    #test2('http://www.ndrugs.com/?s=alodorm')
    #test3()
    
