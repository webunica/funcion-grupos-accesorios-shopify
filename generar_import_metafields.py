import pandas as pd
import re
import json

# Configuración
MAGENTO_CSV = r'C:\Users\studioo\Desktop\00000000000000000000_VICCA\EXPORT-MAGENTO\catalog_product_20260505_204218.csv'
OUTPUT_METAFIELDS = 'shopify_metafields_import.csv'

def slugify(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def main():
    print(f"Procesando relaciones para Metafields desde: {MAGENTO_CSV}")
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)

    metafield_data = []
    current_handle = None
    current_accessories = []

    for _, row in df.iterrows():
        # Si la fila tiene SKU y url_key, es un producto nuevo
        if pd.notna(row['sku']) and pd.notna(row['url_key']):
            # Guardar el producto anterior si tenía accesorios
            if current_handle and current_accessories:
                # Formato de lista para Shopify Metafields (JSON string de handles)
                # Nota: Algunos importadores prefieren una lista separada por comas, 
                # pero el formato estándar de Shopify para listas de referencia es un array JSON.
                metafield_data.append({
                    'Handle': current_handle,
                    'Metafield: custom.accessories [list.product_reference]': json.dumps(list(set(current_accessories)))
                })
            
            # Reset para el nuevo producto
            current_handle = row['url_key']
            current_accessories = []

        # Si la fila tiene un accesorio con precio, lo añadimos
        if pd.notna(row['_custom_option_row_title']) and (row['_custom_option_row_price'] or 0) > 0:
            acc_handle = f"acc-{slugify(row['_custom_option_title'])}-{slugify(row['_custom_option_row_title'])}"
            current_accessories.append(acc_handle)

    # Guardar el último producto procesado
    if current_handle and current_accessories:
        metafield_data.append({
            'Handle': current_handle,
            'Metafield: custom.accessories [list.product_reference]': json.dumps(list(set(current_accessories)))
        })

    # Generar el CSV
    output_df = pd.DataFrame(metafield_data)
    output_df.to_csv(OUTPUT_METAFIELDS, index=False, encoding='utf-8')
    
    print(f"SUCCESS: Archivo de Metafields generado: {OUTPUT_METAFIELDS}")
    print(f"Se han vinculado accesorios a {len(metafield_data)} productos principales.")

if __name__ == "__main__":
    main()
