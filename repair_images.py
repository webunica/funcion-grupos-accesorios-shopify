import pandas as pd
import requests
import json

# ── Configuración ────────────────────────────────────────────────────────────
SHOP_URL = 'vicca-3.myshopify.com'
ACCESS_TOKEN = 'TU_SHOPIFY_TOKEN_AQUI'
MAGENTO_CSV = r'C:\Users\studioo\Desktop\00000000000000000000_VICCA\EXPORT-MAGENTO\catalog_product_20260505_204218.csv'
IMAGE_BASE_URL = 'https://vicca.cl/media/catalog/product'

API_VERSION = '2024-04'
REST_URL = f'https://{SHOP_URL}/admin/api/{API_VERSION}'
HEADERS = {
    'X-Shopify-Access-Token': ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

def main():
    print(f"Reparando imágenes de productos en {SHOP_URL}...")
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)
    
    # Filtrar solo productos base
    main_products = df[df['name'].notna() & df['sku'].notna()].copy()

    for _, row in main_products.iterrows():
        sku = str(row['sku'])
        handle = str(row['url_key']) if pd.notna(row['url_key']) else sku.lower()
        
        # Buscar imagen en varias columnas
        img_path = None
        for col in ['image', 'small_image', 'thumbnail', '_media_image']:
            if col in row and pd.notna(row[col]) and str(row[col]) != 'no_selection' and str(row[col]).startswith('/'):
                img_path = str(row[col])
                break
        
        if not img_path: continue

        # Get product ID
        r_get = requests.get(f"{REST_URL}/products.json?handle={handle}", headers=HEADERS).json()
        if not r_get.get('products'): continue
        
        product = r_get['products'][0]
        if product['images']: 
            # print(f"  [-] {handle} ya tiene imagen.")
            continue

        print(f"  [*] Pegando imagen a {handle} ({img_path})...")
        img_url = f"{IMAGE_BASE_URL}{img_path}"
        
        payload = {
            "product": {
                "id": product['id'],
                "images": [{"src": img_url}]
            }
        }
        
        r_upd = requests.put(f"{REST_URL}/products/{product['id']}.json", headers=HEADERS, json=payload)
        if r_upd.status_code != 200:
            print(f"    Error en {handle}: {r_upd.status_code} - {r_upd.text}")

    print("\nReparación de imágenes finalizada.")

if __name__ == '__main__':
    main()
