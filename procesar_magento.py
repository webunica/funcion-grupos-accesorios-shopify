import pandas as pd
import re
import os

# Configuración de rutas
MAGENTO_CSV = r'C:\Users\studioo\Desktop\00000000000000000000_VICCA\EXPORT-MAGENTO\catalog_product_20260505_204218.csv'
OUTPUT_SHOPIFY = 'shopify_accesorios_import.csv'
OUTPUT_MAPPING = 'vinculacion_productos_accesorios.csv'

def slugify(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def main():
    print(f"Leyendo archivo: {MAGENTO_CSV}...")
    # Cargamos el CSV. Usamos low_memory=False por la cantidad de columnas.
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)

    # 1. GENERAR PRODUCTOS ACCESORIO PARA SHOPIFY
    print("Extrayendo accesorios únicos...")
    
    # Filtramos filas que tengan título de opción y precio de fila > 0
    acc_mask = df['_custom_option_row_title'].notna() & (df['_custom_option_row_price'].fillna(0) > 0)
    accessories_df = df[acc_mask].copy()

    # Deduplicamos por Título de Grupo, Título de Accesorio y Precio
    unique_acc = accessories_df.drop_duplicates(subset=['_custom_option_title', '_custom_option_row_title', '_custom_option_row_price'])

    shopify_rows = []
    for _, row in unique_acc.iterrows():
        opt_group = row['_custom_option_title']
        opt_val = row['_custom_option_row_title']
        price = row['_custom_option_row_price']
        handle = f"acc-{slugify(opt_group)}-{slugify(opt_val)}"
        
        shopify_rows.append({
            'Handle': handle,
            'Title': f"{opt_group}: {opt_val}",
            'Body (HTML)': f"Accesorio opcional de tipo {opt_group} proveniente de Magento.",
            'Vendor': 'Magento Import',
            'Type': opt_group,
            'Tags': 'accesorio-configurador, oculto',
            'Published': 'TRUE',
            'Option1 Name': 'Title',
            'Option1 Value': 'Default Title',
            'Variant SKU': row['_custom_option_row_sku'] if pd.notna(row['_custom_option_row_sku']) else f"ACC-{slugify(opt_val).upper()}",
            'Variant Price': price,
            'Variant Inventory Tracker': 'shopify',
            'Variant Inventory Qty': 9999,
            'Variant Inventory Policy': 'deny',
            'Status': 'active'
        })

    pd.DataFrame(shopify_rows).to_csv(OUTPUT_SHOPIFY, index=False, encoding='utf-8')
    print(f"SUCCESS: CSV para Shopify generado: {OUTPUT_SHOPIFY} ({len(shopify_rows)} productos)")

    # 2. GENERAR MAPEO DE VINCULACIÓN (SKU Producto -> Handle Accesorio)
    print("Generando mapa de vinculación para Metafields...")
    
    mapping_rows = []
    current_sku = None
    
    # Recorremos todo el CSV de Magento para mantener la relación con el SKU principal
    for _, row in df.iterrows():
        if pd.notna(row['sku']):
            current_sku = row['sku']
        
        if pd.notna(row['_custom_option_row_title']) and (row['_custom_option_row_price'] or 0) > 0:
            mapping_rows.append({
                'Parent_SKU': current_sku,
                'Accessory_Group': row['_custom_option_title'],
                'Accessory_Title': row['_custom_option_row_title'],
                'Accessory_Handle': f"acc-{slugify(row['_custom_option_title'])}-{slugify(row['_custom_option_row_title'])}"
            })

    pd.DataFrame(mapping_rows).to_csv(OUTPUT_MAPPING, index=False, encoding='utf-8')
    print(f"SUCCESS: Mapa de vinculación generado: {OUTPUT_MAPPING}")

if __name__ == "__main__":
    main()
