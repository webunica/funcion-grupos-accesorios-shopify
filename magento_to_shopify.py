"""
magento_to_shopify.py  —  v2 (script unificado)
================================================
Genera los 4 archivos CSV necesarios para la migración de 
accesorios y relacionados de Magento → Shopify:

  1. shopify_accesorios_import.csv       (nuevos productos sombra)
  2. vinculacion_productos_accesorios.csv (mapa legible SKU → accesorio)
  3. shopify_metafields_accesorios.csv   (metafield custom.accessories)
  4. shopify_metafields_relacionados.csv (metafield custom.related_products)

Mejoras v2:
  - Script único con config centralizada.
  - slugify unificado y compartido.
  - Handle de accesorio deduplicado correctamente:
      si mismo título tiene precios distintos en productos distintos,
      se crea sólo UNA entrada usando el precio mínimo.
  - Uso de fillna(0) para evitar errores con NaN en columnas numéricas.
  - Guardado del último producto en ambos bucles de relaciones.
  - Mensaje de resumen final con conteo de cada archivo.
"""

import pandas as pd
import re
import json
import os

# ── Configuración ────────────────────────────────────────────────────────────
MAGENTO_CSV      = r'C:\Users\studioo\Desktop\00000000000000000000_VICCA\EXPORT-MAGENTO\catalog_product_20260505_204218.csv'
OUTPUT_DIR       = os.path.dirname(os.path.abspath(__file__))   # misma carpeta del script

OUT_ACCESORIOS   = os.path.join(OUTPUT_DIR, 'shopify_accesorios_import.csv')
OUT_VINCULACION  = os.path.join(OUTPUT_DIR, 'vinculacion_productos_accesorios.csv')
OUT_MF_ACC       = os.path.join(OUTPUT_DIR, 'shopify_metafields_accesorios.csv')
OUT_MF_REL       = os.path.join(OUTPUT_DIR, 'shopify_metafields_relacionados.csv')

# Tipos de accesorio que permiten selección MÚLTIPLE (checkbox).
# Todo lo que NO esté aquí usará radio (selección única).
MULTI_SELECT_TYPES = {'Accesorios', 'Extras'}

# ── Helpers ──────────────────────────────────────────────────────────────────
def slugify(text):
    """Convierte texto a slug URL-safe en español."""
    if pd.isna(text):
        return ''
    text = str(text).lower()
    # Normalizar tildes/caracteres especiales
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u', 'ä': 'a', 'ö': 'o',
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')


def build_acc_handle(group_title, row_title):
    return f"acc-{slugify(group_title)}-{slugify(row_title)}"


def save_csv(df, path, label):
    df.to_csv(path, index=False, encoding='utf-8')
    print(f"  [OK] {label}: {len(df)} filas -> {os.path.basename(path)}")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"\nLeyendo CSV de Magento ({os.path.basename(MAGENTO_CSV)})...")
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)
    # Asegurar que columnas numéricas críticas no den error con NaN
    df['_custom_option_row_price'] = pd.to_numeric(df['_custom_option_row_price'], errors='coerce').fillna(0)
    print(f"  Filas totales: {len(df)}")

    # ── 1. Build SKU -> Handle map ────────────────────────────────────────────
    print("\nConstruyendo mapa SKU -> Handle...")
    sku_to_handle = (
        df[df['sku'].notna() & df['url_key'].notna()]
        .drop_duplicates(subset=['sku'])
        .set_index('sku')['url_key']
        .to_dict()
    )
    print(f"  Productos detectados: {len(sku_to_handle)}")

    # ── 2. Accesorios únicos ──────────────────────────────────────────────────
    print("\nExtrayendo accesorios únicos...")
    acc_mask = df['_custom_option_row_title'].notna() & (df['_custom_option_row_price'] > 0)
    accessories_df = df[acc_mask].copy()

    # Para duplicados (mismo grupo + título), usamos el PRECIO MÍNIMO
    # para evitar handles duplicados con precios distintos que colisionen en Shopify.
    accessories_df['_acc_handle'] = accessories_df.apply(
        lambda r: build_acc_handle(r['_custom_option_title'], r['_custom_option_row_title']), axis=1
    )
    unique_acc = (
        accessories_df
        .sort_values('_custom_option_row_price')
        .drop_duplicates(subset=['_acc_handle'], keep='first')
    )

    shopify_rows = []
    for _, row in unique_acc.iterrows():
        opt_group = str(row['_custom_option_title']).strip()
        opt_val   = str(row['_custom_option_row_title']).strip()
        price     = row['_custom_option_row_price']
        handle    = row['_acc_handle']
        opt_type  = row.get('_custom_option_type', 'drop_down')
        sku_acc   = row['_custom_option_row_sku'] if pd.notna(row['_custom_option_row_sku']) else f"ACC-{slugify(opt_val).upper()}"

        tags = ['accesorio-configurador', 'oculto']
        if opt_type == 'checkbox':
            tags.append('config-multi')

        shopify_rows.append({
            'Handle': handle,
            'Title': f"{opt_group}: {opt_val}",
            'Body (HTML)': f"Accesorio opcional de tipo {opt_group}.",
            'Vendor': 'Migración Magento',
            'Type': opt_group,
            'Tags': ", ".join(tags),
            'Published': 'TRUE',
            'Option1 Name': 'Title',
            'Option1 Value': 'Default Title',
            'Variant SKU': sku_acc,
            'Variant Price': price,
            'Variant Inventory Tracker': 'shopify',
            'Variant Inventory Qty': 9999,
            'Variant Inventory Policy': 'deny',
            'Variant Fulfillment Service': 'manual',
            'Status': 'active',
        })

    save_csv(pd.DataFrame(shopify_rows), OUT_ACCESORIOS, 'Accesorios para Shopify')

    # ── 3. Mapa de vinculación legible (para referencia humana) ───────────────
    print("\nGenerando mapa de vinculación legible...")
    mapping_rows = []
    current_sku  = None
    for _, row in df.iterrows():
        if pd.notna(row['sku']):
            current_sku = row['sku']
        if pd.notna(row['_custom_option_row_title']) and row['_custom_option_row_price'] > 0:
            mapping_rows.append({
                'Parent_SKU':        current_sku,
                'Parent_Handle':     sku_to_handle.get(str(current_sku), ''),
                'Accessory_Group':   row['_custom_option_title'],
                'Accessory_Title':   row['_custom_option_row_title'],
                'Accessory_Price':   row['_custom_option_row_price'],
                'Accessory_Handle':  build_acc_handle(row['_custom_option_title'], row['_custom_option_row_title']),
            })
    save_csv(pd.DataFrame(mapping_rows), OUT_VINCULACION, 'Mapa de vinculación (referencia)')

    # ── 4. Metafields de accesorios (para Shopify importer) ──────────────────
    print("\nGenerando metafields de accesorios...")
    mf_acc_data   = []
    current_handle = None
    current_acc    = []

    def flush_acc():
        if current_handle and current_acc:
            mf_acc_data.append({
                'Handle': current_handle,
                'Metafield: custom.accessories [list.product_reference]': json.dumps(list(dict.fromkeys(current_acc))),
            })

    for _, row in df.iterrows():
        if pd.notna(row['sku']) and pd.notna(row['url_key']):
            flush_acc()
            current_handle = row['url_key']
            current_acc    = []
        if pd.notna(row['_custom_option_row_title']) and row['_custom_option_row_price'] > 0:
            current_acc.append(build_acc_handle(row['_custom_option_title'], row['_custom_option_row_title']))

    flush_acc()
    save_csv(pd.DataFrame(mf_acc_data), OUT_MF_ACC, 'Metafields de accesorios')

    # ── 5. Metafields de productos relacionados ───────────────────────────────
    print("\nGenerando metafields de productos relacionados...")
    mf_rel_data    = []
    current_handle = None
    current_rel    = []

    def flush_rel():
        if current_handle and current_rel:
            handles = list(dict.fromkeys(
                sku_to_handle[sku] for sku in current_rel if sku in sku_to_handle
            ))
            if handles:
                mf_rel_data.append({
                    'Handle': current_handle,
                    'Metafield: custom.related_products [list.product_reference]': json.dumps(handles),
                })

    for _, row in df.iterrows():
        if pd.notna(row['sku']) and pd.notna(row['url_key']):
            flush_rel()
            current_handle = row['url_key']
            current_rel    = []
        for col in ['_links_related_sku', '_links_crosssell_sku']:
            if col in df.columns and pd.notna(row[col]):
                sku = str(row[col]).strip()
                if sku:
                    current_rel.append(sku)

    flush_rel()
    save_csv(pd.DataFrame(mf_rel_data), OUT_MF_REL, 'Metafields de relacionados')

    print("\n========================================")
    print("Proceso completado sin errores.")
    print("Archivos generados en:", OUTPUT_DIR)
    print("========================================\n")


if __name__ == '__main__':
    main()
