import requests
import json

SHOP = 'vicca-3.myshopify.com'
TOKEN = 'TU_SHOPIFY_TOKEN_AQUI'
headers = {'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'}

def main():
    print("Publicando accesorios en Tienda Online...")
    # Buscar productos con la etiqueta 'accesorio-configurador'
    r = requests.get(f'https://{SHOP}/admin/api/2024-04/products.json?tag=accesorio-configurador&limit=250', headers=headers).json()
    
    products = r.get('products', [])
    print(f"Encontrados {len(products)} accesorios.")
    
    for p in products:
        if p['status'] != 'active':
            print(f"  [!] Activando {p['handle']}...")
            requests.put(f'https://{SHOP}/admin/api/2024-04/products/{p["id"]}.json', headers=headers, json={
                "product": {
                    "id": p["id"],
                    "status": "active"
                }
            })
        else:
            print(f"  [OK] {p['handle']} ya está activo.")

if __name__ == '__main__':
    main()
