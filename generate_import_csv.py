import pandas as pd
import os

# ── Configuración ────────────────────────────────────────────────────────────
MAGENTO_CSV = r'C:\Users\studioo\Desktop\00000000000000000000_VICCA\EXPORT-MAGENTO\catalog_product_20260505_204218.csv'
OUTPUT_CSV = r'C:\Users\studioo\Desktop\00000000000000000000_VICCA\GRUPOS-ACCESORIOS\importar_imagenes_shopify.csv'
IMAGE_BASE_URL = 'https://vicca.cl/media/catalog/product'

def main():
    print(f"Generando CSV de reparación de imágenes...")
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)
    
    # Filtrar solo productos base
    main_products = df[df['name'].notna() & df['sku'].notna()].copy()

    shopify_data = []

    for _, row in main_products.iterrows():
        sku = str(row['sku'])
        handle = str(row['url_key']) if pd.notna(row['url_key']) else sku.lower()
        
        # Buscar imagen principal
        img_path = None
        for col in ['image', 'small_image', 'thumbnail']:
            if col in row and pd.notna(row[col]) and str(row[col]) != 'no_selection' and str(row[col]).startswith('/'):
                img_path = str(row[col])
                break
        
        if img_path:
            img_url = f"{IMAGE_BASE_URL}{img_path}"
            title = str(row['name']) if pd.notna(row['name']) else handle
            price = str(row['price']) if pd.notna(row.get('price')) else '0'
            sku = str(row['sku'])
            shopify_data.append({
                'Handle': handle,
                'Title': title,
                'Option1 Name': 'Title',
                'Option1 Value': 'Default Title',
                'Variant SKU': sku,
                'Variant Price': price,
                'Image Src': img_url,
                'Image Command': 'MERGE'
            })

    # Guardar CSV
    output_df = pd.DataFrame(shopify_data)
    output_df.to_csv(OUTPUT_CSV, index=False)
    print(f"CSV generado con éxito en: {OUTPUT_CSV}")
    print(f"Total de imágenes para reparar: {len(shopify_data)}")

if __name__ == '__main__':
    main()
