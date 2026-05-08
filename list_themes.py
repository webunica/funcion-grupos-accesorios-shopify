import requests
import json

SHOP_URL = 'vicca-3.myshopify.com'
ACCESS_TOKEN = 'TU_SHOPIFY_TOKEN_AQUI'
API_VERSION = '2024-04'

url = f'https://{SHOP_URL}/admin/api/{API_VERSION}/themes.json'
headers = {'X-Shopify-Access-Token': ACCESS_TOKEN}

r = requests.get(url, headers=headers)
if r.status_code == 200:
    themes = r.json().get('themes', [])
    for t in themes:
        print(f"ID: {t['id']} | Name: {t['name']} | Role: {t['role']}")
else:
    print(f"Error: {r.status_code} - {r.text}")
