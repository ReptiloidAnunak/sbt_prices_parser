
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json
import os



def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.goto('https://www.mercadolibre.com.ar/tienda/masqueprecios')
    sleep_random(2, 5)

    page.click("#view-more")
    

    with open('prod_page.html', 'w') as file:
        sleep_random(3, 5)
        soup = BeautifulSoup(page.content(), 'html.parser')
        file.write(soup.prettify())
        sleep_random(100, 200)