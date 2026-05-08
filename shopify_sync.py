import pandas as pd
import requests
import json
import re
import os
import time

# ── Configuración ────────────────────────────────────────────────────────────
SHOP_URL = 'vicca-3.myshopify.com'
ACCESS_TOKEN = 'TU_SHOPIFY_TOKEN_AQUI'
MAGENTO_CSV = r'C:\Users\studioo\Desktop\00000000000000000000_VICCA\EXPORT-MAGENTO\catalog_product_20260505_204218.csv'

API_VERSION = '2024-04'
GRAPHQL_URL = f'https://{SHOP_URL}/admin/api/{API_VERSION}/graphql.json'
REST_URL = f'https://{SHOP_URL}/admin/api/{API_VERSION}'

HEADERS = {
    'X-Shopify-Access-Token': ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def slugify(text):
    if pd.isna(text) or str(text).lower() == 'nan': return 'general'
    text = str(text).lower()
    replacements = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ñ':'n'}
    for c, r in replacements.items(): text = text.replace(c, r)
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def build_acc_handle(group_title, row_title):
    g = slugify(group_title)
    r = slugify(row_title)
    return f"acc-{g}-{r}"

def shopify_graphql(query, variables=None):
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json={'query': query, 'variables': variables})
    return response.json() if response.status_code == 200 else None

# ── Phase 1: Create Accessories (REST API for better variant support) ────────
def sync_accessories(unique_acc_df):
    print("\n[Fase 1] Sincronizando productos accesorio (REST)...")
    handle_to_id = {}
    
    for _, row in unique_acc_df.iterrows():
        handle = row['_acc_handle']
        group = str(row['_custom_option_title']).strip() if pd.notna(row['_custom_option_title']) else 'General'
        val = str(row['_custom_option_row_title']).strip()
        title = f"{group}: {val}"
        price = row['_custom_option_row_price']
        opt_type = row.get('_custom_option_type', 'drop_down')
        
        # Check if product exists (GraphQL is fast for check)
        check_query = "{ productByHandle(handle: \""+handle+"\") { id } }"
        res = shopify_graphql(check_query)
        if res and res.get('data', {}).get('productByHandle'):
            print(f"  [-] {handle} ya existe.")
            handle_to_id[handle] = res['data']['productByHandle']['id']
            continue

        # Create product via REST
        print(f"  [+] Creando {handle}...")
        tags = "accesorio-configurador, oculto"
        if opt_type == 'checkbox': tags += ", config-multi"

        payload = {
            "product": {
                "title": title,
                "handle": handle,
                "body_html": f"Accesorio opcional de tipo {group}.",
                "vendor": "Migración Magento",
                "product_type": group,
                "status": "active",
                "tags": tags,
                "variants": [
                    {
                        "price": str(price),
                        "sku": str(row['_custom_option_row_sku']) if pd.notna(row['_custom_option_row_sku']) else f"ACC-{slugify(title).upper()}",
                        "inventory_management": None
                    }
                ]
            }
        }
        
        r = requests.post(f"{REST_URL}/products.json", headers=HEADERS, json=payload)
        if r.status_code == 201:
            # Store handle (not GID) for Phase 2 - handles work in Liquid via all_products
            handle_to_id[handle] = handle
        else:
            print(f"    Error REST en {handle}: {r.status_code} - {r.text}")
            
    return handle_to_id

# ── Phase 2: Link to Parent Products (GraphQL for batch metafields) ──────────
def link_accessories(df, handle_to_id):
    print("\n[Fase 2] Vinculando accesorios a productos principales...")
    
    # Pre-map all Magento products to their accessories
    parent_map = {}
    current_handle = None
    for _, row in df.iterrows():
        if pd.notna(row['sku']) and pd.notna(row['url_key']):
            current_handle = row['url_key']
            if current_handle not in parent_map: parent_map[current_handle] = []
        
        if pd.notna(row['_custom_option_row_title']) and row['_custom_option_row_price'] >= 0:
            acc_h = build_acc_handle(row['_custom_option_title'], row['_custom_option_row_title'])
            if acc_h in handle_to_id:
                parent_map[current_handle].append(acc_h)  # store handle directly

    for p_handle, acc_handles in parent_map.items():
        if not acc_handles: continue
        
        # Deduplicate handles
        acc_handles = list(dict.fromkeys(acc_handles))

        # Find Parent product via REST (simpler, no GID needed)
        r_get = requests.get(f"{REST_URL}/products.json?handle={p_handle}&fields=id", headers=HEADERS).json()
        if not r_get.get('products'):
            continue
        prod_id = r_get['products'][0]['id']
        
        print(f"  [*] Vinculando {len(acc_handles)} accesorios a {p_handle}...")
        
        # Store handles as JSON in a 'json' type metafield - works in Liquid via all_products[handle]
        r_mf = requests.post(
            f"{REST_URL}/products/{prod_id}/metafields.json",
            headers=HEADERS,
            json={"metafield": {
                "namespace": "vicca",
                "key": "accessories",
                "value": json.dumps(acc_handles),
                "type": "json"
            }}
        )
        if r_mf.status_code not in (200, 201):
            print(f"    Error metafield en {p_handle}: {r_mf.status_code}")

# ── Run ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Iniciando sincronización con {SHOP_URL}...")
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)
    df['_custom_option_row_price'] = pd.to_numeric(df['_custom_option_row_price'], errors='coerce').fillna(0)

    # Detect unique accessories
    acc_mask = df['_custom_option_row_title'].notna() & (df['_custom_option_row_price'] >= 0)
    accessories_df = df[acc_mask].copy()
    accessories_df['_acc_handle'] = accessories_df.apply(
        lambda r: build_acc_handle(r['_custom_option_title'], r['_custom_option_row_title']), axis=1
    )
    unique_acc = accessories_df.sort_values('_custom_option_row_price').drop_duplicates(subset=['_acc_handle'], keep='first')

    # Run
    handle_to_id = sync_accessories(unique_acc)
    link_accessories(df, handle_to_id)
    
    print("\nSincronización finalizada.")

if __name__ == '__main__':
    main()
