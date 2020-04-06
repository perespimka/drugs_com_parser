import requests
from bs4 import BeautifulSoup
import json


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'cache-control': 'no-cache'
}

def write_file(obj, fname='rxlist_drugslist_dict.json', meth='w'):
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

def get_drugs_list(i, soup):
    ''' Собираем список всех линков на лекарства, название которых начинается на букву в переменной i,
        возвращаем словарь с ключом в виде буквы, на которую начинается название лекарства и
        значением в виде списка ссылок на описание лекарств
    '''
    result = []
    container = soup.find('div', attrs={'class': 'AZ_results'})
    print(type(container))
    uls = container.find_all('ul')
    for ul in uls:
        lis = ul.find_all('li')
        for li in lis:
            result.append(li.a['href'])            
    return {i: result}

def get_page_url():
    ''' Перебираем страницы с линками на лекарства. Генератор '''
    URL = 'https://www.rxlist.com/drugs/alpha_{}.htm'
    for i in range(97,123):
        yield chr(i), URL.format(chr(i))

def collect_all_links():
    ''' Объединяем все линки на все лекарства, возвращает словарь: ключ - буква, с которой начинается название лекарства,
        значение - список ссылок на препараты
    '''
    generator = get_page_url()
    all_links = {}
    for i, url in generator:
        print('----' + url + '----')
        soup = BeautifulSoup(get_html(url), 'html.parser')
        all_links.update(get_drugs_list(i, soup))
    return all_links

def main():
    all_links = collect_all_links()
    write_file(all_links)


if __name__ == "__main__":
    main()