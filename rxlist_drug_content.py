import requests
from bs4 import BeautifulSoup
from rxlist_collect_links import write_file, get_html
import re


field_names = ['Brand name:', 'Generic name:', ]
URL = "https://www.rxlist.com/b12-drug.htm"
URL2 = 'https://www.rxlist.com/pegintron-and-rebetol-drug.htm'

def components_and_form_re(raw_components):
    '''Регуляркой находим компоненты и формы выпуска препарата.'''
    # Разбиваем на две группы (компоненты) и (формы)
    pattern = r'\((.+?)\)(.*$)'
    try:
        components, forms = re.search(pattern, raw_components).groups()
        components = components.replace(' and ', ' ')
        forms = forms.strip()
        # Проверям на закрытые скобки, добавляем ")", если не хватает
        if components.count('(') > components.count(')'):
            components += ')'
    except AttributeError as er:
        print(f'Ошибка в регулярке: {er}')
        return None
    return components, forms
      
# А тут будет функция, в которой через атрибут  drug_descriptoin.contents мы будем собирать все <p> входящие до следующего блока div
def combine_data(drug_description_contents):
    '''Объединяем данные из абзацев, где могут содержаться components и forms (в случае, если препарат комбинированный)'''
    components, forms = '', ''
    for tag in drug_description_contents:
        if tag.name == 'a':
            break
        else:
            if tag.name == 'p':
                comps_and_forms = components_and_form_re(tag.text)
                if comps_and_forms:
                    if components:
                        components += ', ' + comps_and_forms[0]
                    else:
                        components = comps_and_forms[0]
                    if forms:
                        forms += ', ' + comps_and_forms[1]
                    else:
                        forms = comps_and_forms[1]
    return components, forms
    

def get_data(soup):
    '''Обработка страницы одного лекарства'''
    drug_description = soup.find('div', attrs={'class': 'pgContent'})
    brand_name = drug_description.b.text

    print(combine_data(drug_description.contents))
    #raw_components = drug_description.p.text
    #components_and_form_re(raw_components)

def main():
    pass

if __name__ == "__main__":
    
    soup = BeautifulSoup(get_html(URL2), 'html.parser')
    get_data(soup)
    '''
    components_and_form_re('() abra, cafabra')
    '''