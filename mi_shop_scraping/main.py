import requests
from curl_data import(
    url_mi, 
    headers_mi, 
    cookies_mi, 
    url_re_store, 
    headers_re_store, 
    cookies_re_store,
    data_re_store
)
import os
from bs4 import BeautifulSoup
import time
import random
import json
import csv
import math

"""
- Скрапинг однородной информации (смартфоны) с двух сайтов 
https://mi-shop.com/ru/catalog/smartphones/
https://re-store.ru/apple-iphone/?page=1
-соберу инфрмацию  "card_name" 
                    "card_price",
                    "card_discount"-размер скидки в рублях,
                    "link_on_card"
- запись в один документ (csv, json)
"""


def get_data_mi(url_mi, cookies_mi, headers_mi):
    
    # все запрсы делаю в одной ссесии
    sess = requests.Session()
    
    response = sess.get(url=url_mi, cookies=cookies_mi, headers=headers_mi)
    
    # создаю директорию для сохранения HTML-страницы
    if not os.path.exists("data"):
        os.mkdir("data")
        
    # сохраняю страницу
    with open("data/mi_data.html", "w") as file:
        file.write(response.text)
    
    # инфоблок
    print(f"[INFO_mi] page recorded")    
    
    # читаю страницу
    with open("data/mi_data.html") as file:
        src = file.read()
        
    #  создаю объект BeautifulSoup
    soup = BeautifulSoup(src, "lxml")
    
    # пагинация
    last_page = int(soup.find("nav", class_="w-100").attrs["data-pages"])
    
    # инфоблок
    print(f"[INFO_mi] last page: {last_page}")
    
    # переменная для записи в json
    mi_json_all_data = []
    
    # переменная для записи в csv
    mi_csv_all_data = []
    
    # генерирую ссылки на каждую страницу
    for mi_pagination_page_count in range(1, last_page+1):
    # for mi_pagination_page_count in range(1, 3): # для тестов
        mi_pagination_page_url = f"https://mi-shop.com/ru/catalog/smartphones/page/{mi_pagination_page_count}/"
        
        # делаю запрос к каждой странице
        response = sess.get(url=mi_pagination_page_url, headers=headers_mi, cookies=cookies_mi)
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # общий блок с карточками
        mi_block_cards = soup.find("div", class_="card-horizontal-mutable").find_all("div", class_="bg-white")        
        
        # собираю информацию
        for card in mi_block_cards:
            
            # модель телефона
            try:
                card_name = card.find("div", class_="product-card__title").text.replace("\n", "").strip()
            except Exception as ex:
                card_name = "No name"
            
            # стоимость телефона
            try:
                card_price = card.find("div", class_="price").find("span", class_="price__new").text.replace(" ", "").replace("\n", "")
            except Exception as ex:
                card_price = "No price"
            
            # сумма скидки на телефон
            try:
                card_discount = card.find("div", class_="price").find("div", class_="sale__badge").text
            except Exception as ex:
                card_discount = "No data discount"
            
            # ссылка на телефон
            try:
                link_on_card = f'https://mi-shop.com{card.find("div", class_="product-card__body").find("a").get("href")}'
            except Exception as ex:
                link_on_card = "No data link"
                
            # print(f"Card title: {card_name}\n card_price: {card_price}\n Discount: {card_discount}\n Link: {link_on_card}\n ")
            
            # упаковываю данные для записи в json
            mi_json_all_data.append(
                {
                    "card_name": card_name,
                    "card_price": card_price,
                    "card_discount": card_discount,
                    "link_on_card": link_on_card
                }
                
            )
            
            # упаковываю данные для записи в csv
            mi_csv_all_data.append(
                [
                    card_name,
                    card_price,
                    card_discount,
                    link_on_card
                ]
            )
            
            # рандомная пауза м.у. запросами
            time.sleep(random.randrange(2, 4))
    
        # инфоблок
        print(f"[INFO_mi] complited page {mi_pagination_page_count} of {last_page + 1} ")
            
    # инфоблок
    print(f"[INFO_mi] mi_shop code completed ")
    
    info_tuple = (mi_json_all_data, mi_csv_all_data)
            
    return info_tuple


def get_data_re_store(url_re_store, cookies_re_store, headers_re_store, data_re_store, info_tuple):
    
    # создаю объект сесии
    sess = requests.Session()
    
    response = sess.post(url=url_re_store, cookies=cookies_re_store, headers=headers_re_store, data=data_re_store).json()
    
    # сохраняю страницу в формате json
    with open("data/re_store_data.json", "w") as file:
        json.dump(response, file, indent=4, ensure_ascii=False)
        
    # читаю сохрненную json страницу 
    with open("data/re_store_data.json", "r") as file:
        all_data_product_json = json.load(file)
        
    # пагинация
    # вычленяю из json общее количество смартфонов
    amount_smartphones = all_data_product_json.get("info").get("count")
    
    # делением (на одной странице 30 смартфонов) получаю количество страниц, округляю в большую сторону
    last_page = math.ceil(amount_smartphones / 30)
    
    # инфоблок
    print(f"[INFO_re_store] smartphones: {amount_smartphones}, last page: {last_page}")
    
    # генерирую номера страниц, буду их менять в data_re_store
    for page in range(1, last_page +1):
    # for page in range(1, 3): # для теста
        
        # в "data_re_store" - буду менять  номер страницы
        data_re_store["page"] = page
        
        # делаю запрос к каждой странице
        response = sess.post(url=url_re_store, cookies=cookies_re_store, headers=headers_re_store, data=data_re_store).json()
        
        # общий блок с телефонами
        product_from_page = response.get("products")
        
        # собираю информацию
        for product in product_from_page:
            card_name = product.get("name")
            card_price = product.get("prices").get("current")
            price_old = product.get("prices").get("old")
            
            # вычисляю размер скидки (на сайте есть только старая и новая цена) 
            card_discount =  price_old - card_price
            if card_discount < 0:
                card_discount = 0
            link_on_card = f'https://re-store.ru{product.get("link")}'
            
            # print(f"card_name: {card_name}\n card_price: {card_price}\n price_old: {price_old}\n card_discount: {card_discount}\n link_on_card: {link_on_card}\n{20 * '*'} ")
            
            # упаковываю данные для записи в json
            info_tuple[0].append(
                {
                    "card_name": card_name,
                    "card_price": card_price,
                    "card_discount": card_discount,
                    "link_on_card": link_on_card
                }
            )
            
            # записываю данные в csv
            info_tuple[1].append(
                [
                    card_name,
                    card_price,
                    card_discount,
                    link_on_card
                ]
            )
            
        # пауза между запросами
        time.sleep(random.randrange(1, 3))
            
        # инфоблок
        print(f"[INFO_re_store] complited page {page} of {last_page}")
        
    # записываю csv
    with open("data/all_data.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(
            (
                "card_name",
                "card_price",
                "card_discount",
                "link_on_card"
            )
        )
        writer.writerows(info_tuple[1])
        
    # записываю json
    with open("data/all_data.json", "w") as file:
        json.dump(info_tuple[0], file, indent=4, ensure_ascii=False)
        
    # инфоблок
    print(f"[INFO_re_store] re_store code completed ")
                

def main():
    info_tuple = get_data_mi(url_mi, cookies_mi, headers_mi)
    get_data_re_store(url_re_store, cookies_re_store, headers_re_store, data_re_store, info_tuple)
    
if __name__ == "__main__":
    main()
