# Auth URLs Options by country

# 1:  "https://auth.mercadolibre.com.ar"
# 2:  "https://auth.mercadolivre.com.br"
# 3:  "https://auth.mercadolibre.com.co"
# 4:  "https://auth.mercadolibre.com.mx"
# 5:  "https://auth.mercadolibre.com.uy"
# 6:  "https://auth.mercadolibre.cl"
# 7:  "https://auth.mercadolibre.com.cr"
# 8:  "https://auth.mercadolibre.com.ec"
# 9:  "https://auth.mercadolibre.com.ve"
# 10: "https://auth.mercadolibre.com.pa"
# 11: "https://auth.mercadolibre.com.pe"
# 12: "https://auth.mercadolibre.com.do"
# 13: "https://auth.mercadolibre.com.bo"
# 14: "https://auth.mercadolibre.com.py"

# For example in your app, you can make some like this to get de auth
import urllib

params = urllib.urlencode({'response_type':'code', 'client_id':'5237567377977766', 'redirect_uri':'https://localhost:3000/callback'})
f = urllib.urlopen("https://auth.mercadolibre.com.ar/authorization?%s" % params)
print(f.geturl)