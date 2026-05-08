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
    print(f"Actualizando imágenes de productos SIN imagen en {SHOP_URL}...")
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)
    main_products = df[df['name'].notna() & df['sku'].notna()].copy()

    updated = 0
    skipped = 0
    errors = 0

    for _, row in main_products.iterrows():
        handle = str(row['url_key']) if pd.notna(row['url_key']) else str(row['sku']).lower()

        # Buscar imagen en columnas de Magento
        img_path = None
        for col in ['image', 'small_image', 'thumbnail']:
            val = str(row.get(col, ''))
            if val and val != 'nan' and val != 'no_selection' and val.startswith('/'):
                img_path = val
                break

        if not img_path:
            continue

        # Buscar el producto en Shopify
        r_get = requests.get(
            f"{REST_URL}/products.json?handle={handle}&fields=id,images",
            headers=HEADERS
        ).json()

        if not r_get.get('products'):
            continue

        product = r_get['products'][0]

        # Solo actualizar si NO tiene imagen
        if product.get('images'):
            skipped += 1
            continue

        # Dejar que Shopify descargue la imagen desde vicca.cl
        img_url = f"{IMAGE_BASE_URL}{img_path}"
        print(f"  [→] {handle}")

        r_img = requests.post(
            f"{REST_URL}/products/{product['id']}/images.json",
            headers=HEADERS,
            json={"image": {"src": img_url}}
        )

        if r_img.status_code == 201:
            updated += 1
        else:
            print(f"      Error: {r_img.status_code} - {r_img.text[:100]}")
            errors += 1

    print(f"\n✅ Actualizados: {updated}")
    print(f"⏭️  Ya tenían imagen: {skipped}")
    print(f"❌ Errores: {errors}")

if __name__ == '__main__':
    main()
