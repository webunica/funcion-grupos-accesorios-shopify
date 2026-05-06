import pandas as pd
import json

# Configuración
MAGENTO_CSV = r'C:\Users\studioo\Desktop\00000000000000000000_VICCA\EXPORT-MAGENTO\catalog_product_20260505_204218.csv'
OUTPUT_RELATED = 'shopify_relacionados_import.csv'

def main():
    print(f"Iniciando procesamiento de productos relacionados...")
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)

    # 1. Crear diccionario SKU -> Handle (url_key)
    # Solo tomamos las filas donde hay tanto SKU como url_key
    print("Mapeando SKUs a Handles...")
    sku_to_handle = {}
    for _, row in df.iterrows():
        if pd.notna(row['sku']) and pd.notna(row['url_key']):
            sku_to_handle[str(row['sku']).strip()] = row['url_key']

    # 2. Procesar relaciones
    print("Extrayendo relaciones...")
    related_data = []
    current_handle = None
    current_related_skus = []

    for _, row in df.iterrows():
        # Identificar producto principal
        if pd.notna(row['sku']) and pd.notna(row['url_key']):
            # Guardar el anterior
            if current_handle and current_related_skus:
                # Convertir SKUs de Magento a Handles de Shopify
                related_handles = [sku_to_handle[sku] for sku in current_related_skus if sku in sku_to_handle]
                if related_handles:
                    related_data.append({
                        'Handle': current_handle,
                        'Metafield: custom.related_products [list.product_reference]': json.dumps(related_handles)
                    })
            
            current_handle = row['url_key']
            current_related_skus = []

        # Recolectar SKUs relacionados de esta fila
        # Magento puede tener varios en la misma fila o en filas subsiguientes
        for col in ['_links_related_sku', '_links_crosssell_sku']:
            if col in df.columns and pd.notna(row[col]):
                sku = str(row[col]).strip()
                if sku:
                    current_related_skus.append(sku)

    # Guardar el último
    if current_handle and current_related_skus:
        related_handles = [sku_to_handle[sku] for sku in current_related_skus if sku in sku_to_handle]
        if related_handles:
            related_data.append({
                'Handle': current_handle,
                'Metafield: custom.related_products [list.product_reference]': json.dumps(related_handles)
            })

    # Generar CSV
    output_df = pd.DataFrame(related_data)
    output_df.to_csv(OUTPUT_RELATED, index=False, encoding='utf-8')
    
    print(f"SUCCESS: Archivo de productos relacionados generado: {OUTPUT_RELATED}")
    print(f"Se encontraron relaciones para {len(related_data)} productos.")

if __name__ == "__main__":
    main()
