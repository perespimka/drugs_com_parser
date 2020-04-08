# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from rxlist_collect_links import write_file, get_html
import re
from bs4 import element
from foo import drugs #Тестируем
import logging

logging.basicConfig(filename='log.txt', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

FIELD_CONVERTS = {'INDICATIONS': 'Therapeutic indications', 'DESCRIPTION': None, 
                  'DOSAGE AND ADMINISTRATION': 'Dosage (Posology) and method of administration', 
                  'SIDE EFFECTS': 'Undesirable effects', 'HOW SUPPLIED': None,
                  'DRUG INTERACTIONS': 'Interaction with other medicinal products and other forms of interaction',
                  'WARNINGS': 'Special warnings and precautions for use',
                  'PRECAUTIONS': 'Special warnings and precautions for use', 'OVERDOSE': 'Overdose',
                  'CONTRAINDICATIONS': 'Contraindications', 'CLINICAL PHARMACOLOGY': 'Pharmacodynamic properties',
                  'PATIENT INFORMATION': None, 

                  
}
URL = "https://www.rxlist.com/zagam-drug.htm"
URL2 = 'https://www.rxlist.com/pegintron-and-rebetol-drug.htm'

def components_and_form_re(raw_components):
    '''Регуляркой находим компоненты и формы выпуска препарата и заменяем and'''
    # Разбиваем на две группы (компоненты) и (формы)
    pattern = r'\((.+?)\)(.*)'
    try:
        components, forms = re.search(pattern, raw_components).groups()
        components = components.replace(', and ', ', ')
        components = components.replace(' and ', ', ')
        forms = forms.strip()
        # Проверям на закрытые скобки, добавляем ")", если не хватает
        if components.count('(') > components.count(')'):
            components += ')'
    except AttributeError as er:
        #print(f'Ошибка в регулярке: {er}')
        return None
    return {'components': components, 'forms': forms}
      

def combine_data(first_block_iter):
    '''
    Сбор данных для первого блока
    Объединяем данные из абзацев, где могут содержаться components и forms (в случае, если препарат комбинированный)
    '''
    result = {'components':  '', 'forms': ''}
    try:
        for tag in first_block_iter:
            if tag.name == 'a':
                break
            else:
                if tag.name == 'p':
                    comps_and_forms = components_and_form_re(tag.text)
                    # Сложим строки в случае, если препарат многокомпонентный.
                    if comps_and_forms:
                        for key, val in comps_and_forms.items():
                            if result[key]:
                                result[key] += ', ' + val
                            else:
                                result[key] = val
    except Exception as e:
        logging.debug(f'Ошибка в combine_data: {e}')

    return result

def link_cleaner(tag):
    '''Ссылки превращаем в обычный текст, также ссылки на разделы сайта убираем'''
    links = tag.find_all('a')

def get_data_from_pgContent(pgContent):
    '''Собираем данные из одного блока. Возвращает словарь, ключ - имя поля таблицы описания препарата, значение - содержимое раздела'''
    result = {} # ключ - имя поля в таблице, значение - содержимое раздела
    key = None
    for tag in pgContent.children:
        if isinstance(tag, element.Tag):
            if tag.name == 'h3':
                if tag.text in FIELD_CONVERTS:
                    tag_text = tag.text
                    key = FIELD_CONVERTS[tag_text] #Присваиваем имя поля в таблице как указано в ТЗ (в FIELD_CONVERTS это значения по ключам-разделам сайта)
                    if key: # Проверим, нужен ли нам этот раздел сайта (Есть значение по ключу-разделу сайта в FIELD_CONVERTS)
                        result[key] = ''
                    #Значения разделов WARNINGS и PRECAUTIONS должны объединяться
                    if tag_text == 'WARNINGS' or tag_text == 'PRECAUTIONS':
                        result[key] += f'<h3>{tag_text}</h3>'
                else:
                    key = None
            elif key:
                if tag.name in ['p', 'h4', 'h5']:
                    #тут будет очистка содержимого
                    result[key] += str(tag) # Сохраняем с разметкой. Надо еще чистить ссылки
                elif tag.name == 'center':
                    for child in tag.descendants:
                        if isinstance(child, element.Tag):
                            if child.name == 'table':
                                result[key] += str(child)

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

def get_data(soup):
    '''Обработка страницы одного лекарства. Первый блок pgContent разбираем на drug name, components и forms. Остальные pgContent перебираем 
       и отправляем в get_data_from_pgContent, откуда получаем словарь (этот словарь может иметь несколько ключей): 
       ключ имя поля таблицы описания, значение - само описание. 
       Расширяем результирующий словарь по препарату drug_data словариками из каждого pgContent
    '''

    drug_data = {} # Сюда собираем все разделы в соответствующие поля (ключи словаря)
    pgContent_blocks = soup.find_all('div', attrs={'class': 'pgContent'})
    #drug_data['Drug name'] = pgContent_blocks[0].p.b.text.strip() #ПЛОХО!
    drug_data.update(combine_data(pgContent_blocks[0].children)) #Из первого блока берем components и forms


    foo = True # Проверочная переменная для определения первого блока pgContent
    for pgContent in pgContent_blocks:
        # Пропустим первый блок
        if foo:
            # Из первого блока возьмем первый абзац, в котором содержится имя препарата
            for tag in pgContent.children:
                if tag.name == 'p':
                    #Есть страницы, где нет имени и компонентов/форм в разделах. В таком случае возьмем из заголовка страницы имя препарата
                    try:
                        drug_data['Drug name'] = tag.b.text.strip()
                    except:
                        drug_data['Drug name'] = soup.h1.text
                        logging.debug(f'Имя {drug_data["Drug name"]} взято из резервного источника')
                    break   
            foo = False
            continue
        data_from_pgContent = get_data_from_pgContent(pgContent)
        drug_data.update(data_from_pgContent)
    
    return drug_data


def main():
    for drug in drugs:
        soup = BeautifulSoup(get_html(drug), 'html.parser')
        get_data(soup)
    #write_file(list(HEADERS), fname='HEADERS.json')

if __name__ == "__main__":
    '''
    main()
    '''
    soup = BeautifulSoup(get_html(URL2), 'html.parser')
    write_file(get_data(soup), fname='test_drug_data.json')
