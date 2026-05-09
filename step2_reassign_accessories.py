"""
step2_reassign_accessories.py (v2.2)
==================================
Re-crea los productos accesorios con nombres y handles correctos basados en el grupo Magento,
ASEGURANDO UNICIDAD POR PRECIO (para evitar colisiones de recargos distintos).
Víncula vía metafield `custom.accessories` (GIDs) a los productos principales.
Normaliza los grupos (product_type) a MAYÚSCULAS para evitar duplicados en UI.
"""

import pandas as pd
import requests
import json
import time
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

SHOP = 'vicca-3.myshopify.com'
TOKEN = 'YOUR_TOKEN_HERE'
GQL_URL = f'https://{SHOP}/admin/api/2024-04/graphql.json'
HEADERS = {
    'X-Shopify-Access-Token': TOKEN,
    'Content-Type': 'application/json'
}

MAGENTO_CSV = r'C:\Users\studioo\Desktop\00000000000000000000_VICCA\EXPORT-MAGENTO\catalog_product_20260505_204218.csv'

def graphql_query(query, variables=None):
    for _ in range(3):
        try:
            r = requests.post(GQL_URL, headers=HEADERS, json={'query': query, 'variables': variables})
            res = r.json()
            if 'errors' in res and 'throttled' in str(res).lower():
                time.sleep(2)
                continue
            return res
        except Exception as e:
            time.sleep(2)
    return {}

def slugify(text):
    if pd.isna(text): return ''
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def get_all_main_products():
    """Obtiene mapeo de SKU -> Product GID de todos los productos principales."""
    print("Obteniendo productos principales de Shopify...")
    sku_to_gid = {}
    page_info = None
    
    while True:
        url = f'https://{SHOP}/admin/api/2024-04/products.json'
        params = {'limit': 250, 'fields': 'id,variants,admin_graphql_api_id'}
        if page_info:
            params = {'limit': 250, 'page_info': page_info}
            
        r = requests.get(url, headers=HEADERS, params=params)
        data = r.json()
        
        for p in data.get('products', []):
            gid = p['admin_graphql_api_id']
            for v in p['variants']:
                sku = v.get('sku')
                if sku:
                    sku_to_gid[sku.strip()] = gid
                    
        print(f"  {len(sku_to_gid)} productos cargados...")
        
        link = r.headers.get('Link', '')
        if 'rel="next"' in link:
            match = re.search(r'page_info=([^&>]+)[^>]*>; rel="next"', link)
            if match:
                page_info = match.group(1)
            else:
                break
        else:
            break
        time.sleep(0.3)
        
    return sku_to_gid

def main():
    print("--- PASO 2: RE-CREACIÓN Y REASIGNACIÓN (NORMALIZADO) ---")
    df = pd.read_csv(MAGENTO_CSV, low_memory=False)
    
    accessories_to_create = {}
    product_accessories = {}
    
    current_sku = None
    current_group = None
    
    print("Analizando CSV y corrigiendo grupos...")
    for idx, row in df.iterrows():
        if pd.notna(row['sku']):
            sku_raw = str(row['sku']).strip()
            if sku_raw != current_sku:
                current_sku = sku_raw
                current_group = None
                
        if pd.notna(row['_custom_option_title']):
            current_group = str(row['_custom_option_title']).strip()
            
        if pd.notna(row['_custom_option_row_title']):
            store = row.get('_custom_option_store', None)
            if pd.notna(store):
                continue 

            group = current_group if current_group else 'GENERAL'
            title = str(row['_custom_option_row_title']).strip()
            
            price_val = row['_custom_option_row_price']
            price = float(price_val) if pd.notna(price_val) else 0.0
            
            # NORMALIZACIÓN CLAVE: Todo a MAYÚSCULAS
            p_type = group.upper()
            clean_title_slug = slugify(title)
            
            if p_type in ['GENERAL', '', 'NAN']:
                if 'cuerpo' in clean_title_slug or '-2-' in clean_title_slug or '-3-' in clean_title_slug: p_type = 'CUERPOS'
                elif 'revistero' in clean_title_slug: p_type = 'EXTRA'
                elif 'pata' in clean_title_slug or 'luna' in clean_title_slug or 'split' in clean_title_slug: p_type = 'PATAS'
                elif 'ecocuero' in clean_title_slug or 'tela' in clean_title_slug or 'tapiz' in clean_title_slug: p_type = 'COLOR TAPIZ'
                elif 'brazo' in clean_title_slug: p_type = 'BRAZOS'
                elif 'base' in clean_title_slug: p_type = 'BASE'
                else: p_type = 'OPCIONAL'
            
            p_type_slug = slugify(p_type)[:30]
            t_slug = slugify(title)[:60]
            p_suffix = f"-{int(price)}" if price > 0 else ""
            
            handle = f"acc-{p_type_slug}-{t_slug}{p_suffix}"
            
            if handle not in accessories_to_create:
                accessories_to_create[handle] = {
                    'group': p_type,
                    'title': f"{p_type}: {title}",
                    'price': price
                }
                
            if current_sku:
                if current_sku not in product_accessories:
                    product_accessories[current_sku] = []
                if handle not in product_accessories[current_sku]:
                    product_accessories[current_sku].append(handle)
                    
    print(f"Se encontraron {len(accessories_to_create)} accesorios únicos.")
    
    created_accessories_gids = {}
    
    print("\nVerificando/Creando accesorios en Shopify...")
    for handle, data in accessories_to_create.items():
        payload = {
            "product": {
                "title": data['title'],
                "handle": handle,
                "product_type": data['group'],
                "tags": "accesorio-configurador",
                "status": "active",
                "variants": [{"price": str(data['price'])}]
            }
        }
        gr = requests.get(f"https://{SHOP}/admin/api/2024-04/products.json?handle={handle}", headers=HEADERS).json()
        if gr.get('products'):
            prod = gr['products'][0]
            pid = prod['id']
            created_accessories_gids[handle] = f"gid://shopify/Product/{pid}"
            
            if prod.get('product_type') != data['group']:
                print(f"🔧 Corrigiendo Type: {handle} ({prod.get('product_type')} -> {data['group']})")
                requests.put(f"https://{SHOP}/admin/api/2024-04/products/{pid}.json", 
                             headers=HEADERS, 
                             json={"product": {"id": pid, "product_type": data['group']}})
        else:
            r = requests.post(f"https://{SHOP}/admin/api/2024-04/products.json", headers=HEADERS, json=payload)
            if r.status_code in (200, 201):
                res = r.json()
                pid = res['product']['id']
                created_accessories_gids[handle] = f"gid://shopify/Product/{pid}"
                print(f"✅ Creado: {handle} (${data['price']})")
            else:
                print(f"❌ Error al crear {handle}: {r.text}")
        time.sleep(0.15)
        
    sku_to_gid = get_all_main_products()
    print(f"\nVinculando accesorios a {len(product_accessories)} productos principales...")
    
    for sku, handles in product_accessories.items():
        if not handles: continue
        main_gid = sku_to_gid.get(sku)
        if not main_gid: continue
            
        gids_to_link = []
        for h in handles:
            if h in created_accessories_gids:
                gids_to_link.append(created_accessories_gids[h])
                
        if gids_to_link:
            q = """
            mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
              metafieldsSet(metafields: $metafields) {
                metafields { id }
                userErrors { field message }
              }
            }
            """
            variables = {
                "metafields": [
                    {
                        "ownerId": main_gid,
                        "namespace": "custom",
                        "key": "accessories",
                        "type": "list.product_reference",
                        "value": json.dumps(gids_to_link)
                    }
                ]
            }
            res = graphql_query(q, variables)
            time.sleep(0.1)

    print("\n✅ PASO 2 COMPLETADO (Grupos Normalizados).")

if __name__ == '__main__':
    main()
