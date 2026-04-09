from mercadolibre.client import Client

client = Client(
    '5237567377977766',
    'kcQHqtDeg2aJSPS0uWnOVVvTHyeLSbOg', 
    site='MLA'
)

url = client.authorization_url('https://localhost/callback')

print(url)