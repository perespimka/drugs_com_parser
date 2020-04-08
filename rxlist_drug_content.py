import requests
from bs4 import BeautifulSoup
from rxlist_collect_links import write_file, get_html
import re
from bs4 import element
from foo import drugs #Тестируем


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

def link_cleaner(tag):
    '''Ссылки превращаем в обычный текст, также ссылки на разделы сайта убираем'''
    links = tag.find_all('a')

def get_data_from_pgContent(pgContent):
    '''Собираем данные из одного блока. Возвращает словарь, ключ - имя поля таблицы описания препарата, значение - содержимое раздела'''
    result = {} # ключ - имя поля в таблице, значение - содержимое раздела
    print('*-'*5)
    key = None
    for tag in pgContent.children:
        if isinstance(tag, element.Tag):
            print(f'im here. tag name: {tag.name}, tag.text: {tag.text}')
            if tag.name == 'h3':
                if tag.text in FIELD_CONVERTS:
                    tag_text = tag.text
                    key = FIELD_CONVERTS[tag_text] #Присваиваем имя поля в таблице как указано в ТЗ (в FIELD_CONVERTS это значения по ключам-разделам сайта)
                    if key: # Проверим, нужен ли нам этот раздел сайта (Есть значение по ключу-разделу сайта)
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

    print(result)
    return result

def get_all_headers(pgContent):
    headers = set()
    for tag in pgContent.children:
        if isinstance(tag, element.Tag):
            print(f'im here. tag name: {tag.name}, tag.text: {tag.text}')
            if tag.name == 'h3':
                headers.add(tag.text)
    return headers

HEADERS = set()

def get_data(soup):
    '''Обработка страницы одного лекарства'''

    drug_data = {} # Сюда собираем все разделы в соответствующие поля (ключи словаря)
    pgContent_blocks = soup.find_all('div', attrs={'class': 'pgContent'})
    print(pgContent_blocks[0].p)
    drug_data['Drug name'] = pgContent_blocks[0].p.b.text.strip() #ПЛОХО!
    
    drug_data.update(combine_data(pgContent_blocks[0].children)) #Из первого блока берем components и forms
    print(drug_data)
    foo = True 
    for pgContent in pgContent_blocks:
        # Пропустим первый блок
        if foo:
            foo = False
            continue
        HEADERS.update(get_all_headers(pgContent))
        
        #get_data_from_pgContent(pgContent)
        #break

def main():
    for drug in drugs:
        soup = BeautifulSoup(get_html(drug), 'html.parser')
        get_data(soup)
    write_file(list(HEADERS, fname='HEADERS.json'))

if __name__ == "__main__":

    main()
    '''
    soup = BeautifulSoup(get_html(URL2), 'html.parser')
    get_data(soup)
    '''