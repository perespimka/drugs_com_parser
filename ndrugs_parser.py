from bs4 import BeautifulSoup, element
from rxlist_collect_links import write_file, get_html
import logging
import re

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
              'CR price estimates', 'CR time for results', 'CR reported age', 'USES_2', 'DOSAGE_2', 'SIDE EFFECTS_2', 'Pregnancy', 'Overdose', 'Actions'
)


def get_main_tab_data(content, name):
    headers = [header.format(name) for header in HEADERS]
    fields_convert = dict(zip(headers, HEADER_VALUES))
    key = None
    result = {}
    for tag in content.children:
        if isinstance(tag, element.Tag):
            if tag.name == 'h2':
                if tag.text in fields_convert:
                    key = fields_convert[tag.text]
                    if key not in result:# Создадим пустые строки в новых ключах для возможности добавления строк
                        result[key] = ''                    
                else:
                    key = None
            elif tag.name == 'table' and tag.attrs.get('class')[0] == 'brd':
                result['LIST OF  SUBSTITUTES (BRAND AND GENERIC NAMES)'] += str(tag).strip()
                continue
            elif key:
                if tag.name in ['p', 'h4', 'h5', 'ul', 'center', 'b', 'ol']:
                    result[key] += str(tag).strip()
    return result

def get_page_data(soup):
    name = soup.h1
    name = re.search(r'^(.+) Uses', name.text).group(1)
    content = soup.find('div', attrs={'class': 'content'})
    result = get_main_tab_data(content, name)


                
                           

def main():
    link = 'https://www.ndrugs.com/?s=bendazol'
    soup = BeautifulSoup(get_html(link), 'lxml')
    get_page_data(soup)

if __name__ == "__main__":
    main()

