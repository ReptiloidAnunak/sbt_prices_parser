

from data_base.models import Product
from bs4 import BeautifulSoup



with open('Pala Elice Ventilador Liliana Vvtfc18 18p 5 Aspas _ Envío gratis', 'r') as file:
    content = file.read()
    soup = BeautifulSoup(content, 'html.parser')
    print(soup)
    session = SessionLocal()
