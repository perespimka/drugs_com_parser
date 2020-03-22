import requests
from bs4 import BeautifulSoup
import json


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'cache-control': 'no-cache'
}

'''
def generate_alphabet():
    alphabet = [chr(i) for i in range(97,123)]
    print(alphabet)
'''
def write_file(obj, fname='output.json', meth='w'):
    with open(fname, meth) as f:
        if type(obj) in [dict, list]:
            json.dump(obj, f, indent=4)
        elif type(obj) is str:
            f.write(obj)

def get_html(url):
    '''Вернем текст страницы '''
    r = requests.get(url)
    print(r.status_code)
    print(url)
    return r.text

def get_drugs_list(soup):
    ''' Собираем список всех линков на лекарства на странице'''

    ul = soup.find('ul', attrs={'class': 'ddc-list-column-2'})
    if not ul:
        ul = soup.find('ul', attrs={'class': 'ddc-list-unstyled'})
    lis = ul.find_all('li')
    print(f'length of list is {len(lis)}')
    result = []
    for li in lis:
        result.append(li.a['href'])
    return result

def checking_page(soup):
    ''' Проверим, есть на странице описания лекарств (проверяем на отсутствие блока "Popular"), True если есть '''

    checking_block = soup.find('h2', attrs={'class': 'mgt-0'})
    if checking_block:
        return False
    return True
    
def get_page_url():
    ''' Перебираем страницы с линками на лекарства. Генератор '''
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    URL = 'https://www.drugs.com/alpha/{}.html'
    for i in alphabet:
        for j in alphabet:
            yield URL.format(i+j)

def collect_all_links():
    ''' Собираем все линки на все лекарства '''
    generator = get_page_url()
    all_links = []
    for url in generator:
        print('----' + url + '----')
        soup = BeautifulSoup(get_html(url), 'html.parser')
        if checking_page(soup):
            all_links.extend(get_drugs_list(soup))
    return all_links

def main():
    '''Сохраняем в json '''
    all_links = collect_all_links()
    write_file(all_links)


if __name__ == "__main__":
    main()