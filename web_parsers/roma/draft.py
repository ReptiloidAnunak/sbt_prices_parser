from bs4 import BeautifulSoup




# -----------------------------





with open('roma.html', 'r') as file:
    links = generate_pagination_links(file.read())
    print(links)