
from bs4 import BeautifulSoup
import requests
import time
from settings import HEADERS
from data_base.tools import get_products, get_products_all
from data_base.models import Product


file = "Pala Elice Ventilador Liliana Vvtfc18 18p 5 Aspas _ Envío gratis.html"

def get_categories_tree(soup: BeautifulSoup):
    breadcrumb_els= [li.text for li in soup.find('div', 'ui-pdp-breadcrumb').find("ol").find_all('li')]
    return breadcrumb_els


def get_sales_amount(soup:  BeautifulSoup):
    sales_str = soup.find('div', class_='ui-pdp-header plugin__reviews').find('span', class_='ui-pdp-subtitle').text.split('|')[-1]
    sales_amount = sales_str.strip().split(' ')[0]
    print(sales_amount)

with open(file, "r") as f:
    content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    get_sales_amount(soup)


def get_categories_tree(soup: BeautifulSoup):
    breadcrumb_els= [li.text for li in soup.find('div', 'ui-pdp-breadcrumb').find("ol").find_all('li')]
    return breadcrumb_els


def get_sales_amount(soup:  BeautifulSoup):
    sales_str = soup.find('div', class_='ui-pdp-header plugin__reviews').find('span', class_='ui-pdp-subtitle').text.split('|')[-1]
    sales_amount = sales_str.strip().split(' ')[0]
    return sales_amount

def get_prod_details(product: Product):
    time.sleep(2)
    session = requests.Session()
    response = session.get(product.url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")
    try:

        categories_lst = get_categories_tree(soup)
        print(categories_lst)
        sales_amount = get_sales_amount(soup)
        print(sales_amount)
    except AttributeError:
        with open('error.html',  'w') as file:
            file.write(soup.prettify())

def parse_rpoduct():
    products = get_products_all()
    
    for prod in products:
        print(prod.url)
        get_prod_details(prod)
        time.sleep(5)

parse_rpoduct()
    


