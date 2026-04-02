from main import get_prods
with open('prods_grid.html', 'r') as file:
    content = file.read()
    prods = get_prods(content)
    print(prods)