import pandas as pd
import requests
import json
import os
import re

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

def clean_html(text):
    if pd.isna(text): return ""
    return str(text)

def main():
    print(f"Iniciando importación de productos base a {SHOP_URL}...")
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)
    
    # Filtrar solo productos base (tienen SKU y Nombre)
    # En Magento export, la fila del producto principal tiene todos los datos. 
    # Las filas de opciones suelen tener SKU pero no nombre de producto principal.
    main_products = df[df['name'].notna() & df['sku'].notna()].copy()
    print(f"Total de productos base encontrados: {len(main_products)}")

    for _, row in main_products.iterrows():
        sku = str(row['sku'])
        handle = str(row['url_key']) if pd.notna(row['url_key']) else sku.lower()
        title = str(row['name'])
        
        # Check if already exists
        check = requests.get(f"{REST_URL}/products.json?handle={handle}", headers=HEADERS).json()
        if check.get('products'):
            print(f"  [-] {handle} ya existe, saltando...")
            continue

        print(f"  [+] Subiendo {title} (SKU: {sku})...")
        
        # Build image list
        images = []
        if pd.notna(row['image']) and str(row['image']) != 'no_selection':
            img_url = f"{IMAGE_BASE_URL}{row['image']}"
            images.append({"src": img_url})

        # Product payload
        payload = {
            "product": {
                "title": title,
                "handle": handle,
                "body_html": clean_html(row['description']),
                "vendor": "VICCA",
                "product_type": str(row['_attribute_set']) if pd.notna(row['_attribute_set']) else "Muebles",
                "status": "active",
                "tags": "magento-import, base-product",
                "variants": [
                    {
                        "sku": sku,
                        "price": str(row['price']),
                        "weight": float(row['weight']) if pd.notna(row['weight']) else 0.0,
                        "inventory_management": "shopify",
                        "inventory_policy": "continue"
                    }
                ],
                "images": images
            }
        }

        r = requests.post(f"{REST_URL}/products.json", headers=HEADERS, json=payload)
        if r.status_code == 201:
            # Set inventory (optional)
            if pd.notna(row['qty']):
                new_prod = r.json()['product']
                variant_id = new_prod['variants'][0]['id']
                inv_item_id = new_prod['variants'][0]['inventory_item_id']
                # find location
                loc_res = requests.get(f"{REST_URL}/locations.json", headers=HEADERS).json()
                if loc_res.get('locations'):
                    loc_id = loc_res['locations'][0]['id']
                    inv_payload = {
                        "location_id": loc_id,
                        "inventory_item_id": inv_item_id,
                        "available": int(float(row['qty']))
                    }
                    requests.post(f"{REST_URL}/inventory_levels/set.json", headers=HEADERS, json=inv_payload)
        else:
            print(f"    Error en {sku}: {r.status_code} - {r.text}")

    print("\nImportación de productos base finalizada.")

if __name__ == '__main__':
    main()
