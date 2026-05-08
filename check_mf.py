import requests
SHOP = 'vicca-3.myshopify.com'
TOKEN = 'TU_SHOPIFY_TOKEN_AQUI'
headers = {'X-Shopify-Access-Token': TOKEN}

r = requests.get(f'https://{SHOP}/admin/api/2024-04/products.json?handle=silla-black', headers=headers).json()
if r.get('products'):
    pid = r['products'][0]['id']
    mf = requests.get(f'https://{SHOP}/admin/api/2024-04/products/{pid}/metafields.json', headers=headers).json()
    for m in mf.get('metafields', []):
        print(f"{m['namespace']}.{m['key']}: {m['value']}")
else:
    print('Not found')
