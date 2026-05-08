import requests
SHOP_URL = 'vicca-3.myshopify.com'
ACCESS_TOKEN = 'TU_SHOPIFY_TOKEN_AQUI'
API_VERSION = '2024-04'
url = f'https://{SHOP_URL}/admin/api/{API_VERSION}/shop.json'
headers = {'X-Shopify-Access-Token': ACCESS_TOKEN}
r = requests.get(url, headers=headers)
print(r.status_code)
print(r.text)
