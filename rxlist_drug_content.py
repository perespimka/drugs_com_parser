# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from rxlist_collect_links import write_file, get_html
import re
from bs4 import element
from rxlist_write_csv import FORMS_LIST, SMALL_FORMS_LIST
import logging
import json
import copy
import pandas as pd


logging.basicConfig(filename='log.txt', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

FIELD_CONVERTS = {'INDICATIONS': 'Therapeutic indications', 'DESCRIPTION': None, 
                  'DOSAGE AND ADMINISTRATION': 'Dosage (Posology) and method of administration', 
                  'SIDE EFFECTS': 'Undesirable effects', 'HOW SUPPLIED': 'Special precautions for disposal and other handling',
                  'DRUG INTERACTIONS': 'Interaction with other medicinal products and other forms of interaction',
                  'WARNINGS': 'Special warnings and precautions for use',
                  'PRECAUTIONS': 'Special warnings and precautions for use', 'OVERDOSE': 'Overdose',
                  'CONTRAINDICATIONS': 'Contraindications', 'CLINICAL PHARMACOLOGY': 'Pharmacodynamic properties',
                  'PATIENT INFORMATION': None, 'ADVERSE REACTIONS': None
}


def clean_string_from_shit(string):
    '''Очистка от переносов строк и лишних пробелов'''
    string = string.strip()
    string = string.replace('\n', '')
    lst = string.split()
    string = ' '.join(lst)
    return string

def clean_and(components):
    components = components.replace(', and ', ', ')
    components = components.replace(' and ', ', ')
    return components

def replace_square_brackets(string):
    return string.replace('[', '(').replace(']', ')')

def components_and_form_re(tag):
    '''
        Функция для первого блока pgContent. Принимает абзац.
        Регуляркой находим компоненты   препарата и заменяем and
    '''
    # Из копии первого абзаца вырезаем тег <b>, так как парсер часто проглатывает тег <br> и проверка начала строки перед скобками не выполняется
    # Поиск выполняем по копии
    tags_copy = copy.copy(tag)
    try:
        tags_copy.b.decompose()
    except:
        logging.info('В первом абзаце отсутствует тег <b>')
    raw_components = tags_copy.text
    raw_components = replace_square_brackets(raw_components)
    patterns = (
        r'^\s*\((.+)\)(.*\(.+\).*)',
        r'^\s*\((.+)\)(.*)'
    )
    for pattern in patterns:
        search_result = re.search(pattern, raw_components, flags=re.MULTILINE | re.DOTALL)
        if search_result:
            components, paragraph_forms = search_result.groups()
            components = clean_and(components)
            # Проверям на закрытые скобки, добавляем ")", если не хватает
            if components.count('(') > components.count(')'):
                components += ')'
            return {'Components': components, 'First paragraph forms': paragraph_forms}
    return None

      

def combine_data(first_block_iter):
    '''
    Сбор данных для первого блока
    Объединяем данные из абзацев, где могут содержаться components  (в случае, если препарат комбинированный)
    '''
    result = {'Components':  '', 'First paragraph forms': ''}
    try:
        for tag in first_block_iter:
            if tag.name == 'a':
                break
            elif tag.name == 'p':
                comps_and_forms = components_and_form_re(tag)
                # Сложим строки в случае, если препарат многокомпонентный.
                if comps_and_forms:
                    comps_and_forms['First paragraph forms'] = clean_string_from_shit(comps_and_forms['First paragraph forms'])
                    for key, val in comps_and_forms.items():
                        if result[key]:
                            result[key] += ', ' + val
                        else:
                            result[key] = val
    except Exception as e:
        logging.debug(f'Ошибка в combine_data: {e}')
    return result



def attrs_cleaner(tag):
    '''Очистка атрибутов'''
    NAMES_TO_CLEAN = ['class']    
    
    if isinstance(tag, element.Tag):
        tag.attrs = { key:val for key,val in tag.attrs.items() if key not in NAMES_TO_CLEAN}


def link_to_text(a):
    '''Меняет ссылку на текст'''
    sub = BeautifulSoup(a.text, 'html.parser')
    a.replace_with(sub)

def cut_section_links_1(tag):
    pattern1 = r'\([Ss]ee.+?\)'
    pattern2 = r'[Ss]ee.+\.?'
    string_tag = str(tag)
    string_tag = replace_square_brackets(string_tag)
    new_string = re.sub(pattern1, '', string_tag, flags=re.DOTALL)
    new_string = re.sub(pattern2, '', new_string, flags=re.DOTALL)
    new_soup = BeautifulSoup(new_string, 'html.parser')

    #tag.replace_with(new_soup)
    #Здесь не срабатывает replace_with, приходится менять через insert с очисткой unwrap
    tag.string = '' 
    tag.insert(0,new_soup)
    tag.contents[0].unwrap()

def link_cleaner(tag):
    '''Ссылки превращаем в обычный текст, также ссылки на разделы сайта убираем'''
    links = tag.find_all('a')
    for link in links:
        link_to_text(link)



def get_data_from_pgContent(pgContent):
    '''Собираем данные из одного блока. Возвращает словарь, ключ - имя поля таблицы описания препарата, значение - содержимое раздела'''
    result = {} # ключ - имя поля в таблице, значение - содержимое раздела
    key = None # Переменная, определяющая в какой ключ словаря мы сохраняем содержимое тега. Если None - не сохраняем
    '''
    p_with_align = pgContent.find_all('p', attrs={'align': 'center'}) #Ошибка soup, тег p align="center" не закрывается там, где должен. необходимо его развернуть
    for p in p_with_align:
        p.unwrap()
    '''
    for tag in pgContent.children:
        if isinstance(tag, element.Tag):
            if tag.name == 'h3':
                if tag.text in FIELD_CONVERTS:
                    tag_text = tag.text
                    key = FIELD_CONVERTS[tag_text] #Присваиваем имя поля в таблице как указано в ТЗ (в FIELD_CONVERTS это значения по ключам-разделам сайта)
                    if key: # Проверим, нужен ли нам этот раздел сайта (Есть значение по ключу-разделу сайта в FIELD_CONVERTS)
                        if key not in result:
                            result[key] = ''
                    #Значения разделов WARNINGS и PRECAUTIONS должны объединяться
                    if tag_text == 'WARNINGS' or tag_text == 'PRECAUTIONS':
                        result[key] += f'<h3>{tag_text}</h3>'
                else:
                    key = None
            elif key:
                if tag.name in ['p', 'h4', 'h5', 'ul', 'center', 'b', 'ol']:
                    link_cleaner(tag) # Чистим ссылки
                    cut_section_links_1(tag)
                    attrs_cleaner(tag) 
                    for taggy in tag.descendants:
                        attrs_cleaner(taggy)
                    result[key] += str(tag).strip() # Сохраняем с разметкой.
    return result

"""
def get_all_headers(pgContent):
    '''Служебная функция. Соберем все попадающиеся заголовки <h3>'''
    headers = set()
    for tag in pgContent.children:
        if isinstance(tag, element.Tag):
            if tag.name == 'h3':
                headers.add(tag.text)
    return headers
"""
#HEADERS = set()

def try_to_find_forms(string, FORMS_LIST):
    '''Проверяем строку на наличие известных форм, возвращаем список найденных форм'''
    result = []
    if string:
        for form in FORMS_LIST:
            pattern = r'\b' + f'{form}' + r's{0,1}' + r'\b'
            search_result = re.search(pattern, string, flags=re.IGNORECASE)
            if search_result:
                result.append(form)
    return result

def form_finder(soup, drug_data):
    '''
    Поиск известных нам форм в трех местах - заголовок страницы, первый абзац и How supplied.
    Если находим в заголовке - вырезаем оттуда
    '''
    result = []
    drug_data['Forms'] = ''
    generic_name_tag = soup.find('li', attrs={'itemprop': 'name'}).span
    generic_name = generic_name_tag.text
    result.extend(try_to_find_forms(generic_name, FORMS_LIST))
    if len(result) > 0:
        drug_data['Forms'] = ', '.join(list(set(result)))
        for form in result:
            pattern = r'\b' + f'{form}' + r's{0,1}' + r'\b' #Убираем s в конце слова, например tablets, capsules
            generic_name = re.sub(pattern, '', generic_name, flags=re.IGNORECASE)
        generic_name_tag.string = generic_name
    else:
        result.extend(try_to_find_forms(drug_data['First paragraph forms'], FORMS_LIST))
        if len(result) > 0:
            drug_data['Forms'] = ', '.join(list(set(result))) 
        else:
            try:
                result.extend(try_to_find_forms(drug_data['Special precautions for disposal and other handling'], SMALL_FORMS_LIST))
                drug_data['Forms'] = ', '.join(list(set(result))) 
            except:
                pass

def get_brand_name(soup):
    try:
        brand_name = soup.find_all('li', attrs={'itemprop': 'name'})[1].span.text
    except:
        brand_name = ''
    return brand_name

def compare_names(*names):
    '''Из входящих имен оставим непустые, из них выберем кратчайшее'''
    
    true_names = [name.strip() for name in names if name]
    if len(true_names) > 0:
        min_name = true_names[0]
        for name in true_names:
            if len(name) < len(min_name):
                min_name = name
        return min_name
    else:
        return "NoName"
            


def get_drug_name(pgContent, drug_data, soup):
    '''Из первого блока возьмем первый абзац, в котором содержится имя препарата'''
    try:
        brand_name = get_brand_name(soup).strip()
    except:
        brand_name = ''
    name_from_p = ''
    for tag in pgContent.children:
        if tag.name == 'p':
            #Есть страницы, где нет имени и компонентов/форм в разделах. В таком случае возьмем из заголовка страницы имя препарата
            try:
                name_from_p = tag.b.text.strip() # drug_data['Drug name']
            except:
                name_from_p = brand_name
            name_from_h = soup.h1.text
            break  
    drug_data['Drug name'] =  compare_names(brand_name, name_from_p) 
            
    

def get_components(soup, drug_data):
    components_from_generic = soup.find('li', attrs={'itemprop': 'name'}).span.text
    components_from_first_p = drug_data['Components']
    drug_data['Components'] = clean_and(compare_names(components_from_first_p, components_from_generic))

def letter_gen(x,y):
    '''a-z : range(97,123)'''
    for i in range(x, y):
        yield chr(i)


def get_data(soup):
    '''
        Обработка страницы одного лекарства. Первый блок pgContent разбираем на drug name, components и forms. Остальные pgContent перебираем 
        и отправляем в get_data_from_pgContent, откуда получаем словарь (этот словарь может иметь несколько ключей): 
        ключ имя поля таблицы описания, значение - само описание. 
        Расширяем результирующий словарь по препарату drug_data словариками из каждого pgContent
    '''
    drug_data = {} # Сюда собираем все разделы в соответствующие поля (ключи словаря)
    pgContent_blocks = soup.find_all('div', attrs={'class': 'pgContent'})
    try:
        drug_data.update(combine_data(pgContent_blocks[0].children)) #Из первого блока берем components и forms
        get_drug_name(pgContent_blocks[0], drug_data, soup)
    except:
        logging.info('Страница не содержит блоков pgContent')
        return None
    last_reviewed = soup.find('div', attrs={'class':'monolastreviewed'}).span.text #Дата релиза описания на сайте
    drug_data['Date of revision of the text'] = last_reviewed
    #Перебираем блоки pgContent начиная со второго
    for pgContent in pgContent_blocks[1:]:
        data_from_pgContent = get_data_from_pgContent(pgContent)
        #Т.к. содержимое одного раздела может находиться в разных блоках pgContent мы не делаем drug_data.update(), а проверяем, существует ли ключ
        for key in data_from_pgContent:
            if key in drug_data:
                drug_data[key] += data_from_pgContent[key]
            else:
                 drug_data[key] = data_from_pgContent[key]

    form_finder(soup, drug_data) #Поиск форм
    get_components(soup, drug_data)
    return drug_data


def main():
    with open('rxlist_links_dict_nodoubles.json') as f:
        all_links = json.load(f)
    letters = letter_gen(113, 114) # 97, 223 - все строчные латинские буквы
    
    for letter in letters:
        result = [] #Список из словарей, получаемых get_data 
        for link in all_links[letter]:
            soup = BeautifulSoup(get_html(link), 'lxml')
            drug_data = get_data(soup)
            if drug_data:
                result.append(drug_data)
        pd_to_write = pd.DataFrame(result)
        xlsx_fname = f'rxlist_results_{letter}.xlsx'
        pd_to_write.to_excel(xlsx_fname, index=None, header=True)
        write_file(result, fname=f'rxlist_{letter}_data_json.json')

# TESTS 
def test_components(url):
    soup = BeautifulSoup(get_html(url), 'lxml')
    write_file(soup.prettify(), 'drug_page.html')
    test_res = get_data(soup)
    write_file(test_res, fname='test_1.json')

def collect_forms():
    result = [] 
    for link in r_links:
        soup = BeautifulSoup(get_html(link), 'html.parser')
        drug_data = {} # Сюда собираем все разделы в соответствующие поля (ключи словаря)
        pgContent_blocks = soup.find_all('div', attrs={'class': 'pgContent'})
        drug_data.update(combine_data(pgContent_blocks[0].children))
        if drug_data['Forms']:
            result.append(drug_data['Forms'])
    write_file(result, fname='list_of_forms2.json')

URL = "https://www.rxlist.com/zagam-drug.htm"
URL2 = 'https://www.rxlist.com/pegintron-and-rebetol-drug.htm'
URL3 = 'https://www.rxlist.com/quinidex-drug.htm'
URL4 = 'https://www.rxlist.com/gardasil-drug.htm'
URL5 = 'https://www.rxlist.com/xarelto-drug.htm'
URL6 = 'https://www.rxlist.com/viadur-drug.htm'
URL7 = 'https://www.rxlist.com/navelbine-drug.htm'
URL8 = 'https://www.rxlist.com/quadracel-drug.htm'
URL9 = 'https://www.rxlist.com/nuwiq-drug.htm'
URL10 = 'https://www.rxlist.com/ryzolt-drug.htm'
URL11 = 'https://www.rxlist.com/alora-drug.htm'

if __name__ == "__main__":
    #main()
    test_components(URL11)
    #collect_forms()
    #soup = BeautifulSoup(get_html(URL2), 'html.parser')
    #write_file(get_data(soup), fname='test_drug_data.json')

