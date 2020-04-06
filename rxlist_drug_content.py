import requests
from bs4 import BeautifulSoup
from rxlist_collect_links import write_file, get_html
import re


FIELD_CONVERTS = {'INDICATIONS': 'Therapeutic indications'}
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
        print(f'Ошибка в регулярке: {er}')
        return None
    return {'components': components, 'forms': forms}
      

def combine_data(drug_description_contents):
    '''
    Сбор данных для первого блока
    Объединяем данные из абзацев, где могут содержаться components и forms (в случае, если препарат комбинированный)
    '''
    result = {'components':  '', 'forms': ''}
    for tag in drug_description_contents:
        if tag.name == 'a':
            break
        else:
            if tag.name == 'p':
                print(tag.text)
                comps_and_forms = components_and_form_re(tag.text)
                # Сложим строки в случае, если препарат многокомпонентный.
                if comps_and_forms:
                    for key, val in comps_and_forms.items():
                        if result[key]:
                            result[key] += ', ' + val
                        else:
                            result[key] = val

    return result

def get_data_from_pgContent(pgContent):
    result = {}
    for tag in pgContent.contents:
        if tag.name == 'h3' and tag.text in FIELD_CONVERTS:
            key = FIELD_CONVERTS[tag.text]
            result[key] = ''
        if tag.name == 'p' or 'h4' or 'h5':
            result[key] += str(tag) # Сохраняем с разметкой. Надо еще чистить ссылки

    

def get_data(soup):
    '''Обработка страницы одного лекарства'''
    drug_data = {} # Сюда собираем все разделы в соответствующие поля (ключи словаря)
    pgContent_blocks = soup.find_all('div', attrs={'class': 'pgContent'})
    drug_data['Drug name'] = pgContent_blocks[0].p.b.text.strip()
    drug_data.update(combine_data(pgContent_blocks[0].contents)) #Из первого блока берем components и forms
    print(drug_data)
    foo = True 
    for pgContent in pgContent_blocks:
        # Пропустим первый блок
        if foo:
            foo = False
            continue
        get_data_from_pgContent(pgContent)

def main():
    pass

if __name__ == "__main__":
    
    soup = BeautifulSoup(get_html(URL2), 'html.parser')
    get_data(soup)
