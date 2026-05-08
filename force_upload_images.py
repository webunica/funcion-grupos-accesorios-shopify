import pandas as pd
import requests
import json
import base64
import time

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

# User agent para saltar el bloqueo 406
UA_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def main():
    print(f"Iniciando subida FORZADA de imágenes a {SHOP_URL}...")
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
        if product['images']: continue

        print(f"  [*] Descargando y subiendo imagen para {handle}...")
        img_url = f"{IMAGE_BASE_URL}{img_path}"
        
        try:
            # Descargar imagen localmente con User-Agent
            img_res = requests.get(img_url, headers=UA_HEADERS, timeout=15)
            if img_res.status_code == 200:
                # Convertir a Base64 para subir directamente a Shopify
                img_base64 = base64.b64encode(img_res.content).decode('utf-8')
                
                payload = {
                    "image": {
                        "attachment": img_base64,
                        "filename": img_path.split('/')[-1]
                    }
                }
                
                # Subir a la galería del producto
                r_upd = requests.post(f"{REST_URL}/products/{product['id']}/images.json", headers=HEADERS, json=payload)
                if r_upd.status_code != 201:
                    print(f"    Error subida en {handle}: {r_upd.status_code} - {r_upd.text}")
                else:
                    print(f"    [OK] Imagen subida.")
            else:
                print(f"    Error descarga en {handle}: {img_res.status_code}")
        except Exception as e:
            print(f"    Error fatal en {handle}: {str(e)}")

    print("\nSubida forzada de imágenes finalizada.")

if __name__ == '__main__':
    main()
