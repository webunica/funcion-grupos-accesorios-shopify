import requests
import json

SHOP = 'vicca-3.myshopify.com'
TOKEN = 'TU_SHOPIFY_TOKEN_AQUI'
URL = f'https://{SHOP}/admin/api/2024-04/graphql.json'
headers = {'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'}

mutation = """
mutation {
  metafieldDefinitionCreate(definition: {
    name: "Accesorios del Producto"
    namespace: "custom"
    key: "accessories"
    type: "list.product_reference"
    description: "Lista de productos accesorios configurables vinculados"
    ownerType: PRODUCT
  }) {
    createdDefinition {
      id
      name
      namespace
      key
      type { name }
    }
    userErrors {
      field
      message
    }
  }
}
"""

r = requests.post(URL, headers=headers, json={'query': mutation})
print(f'Status: {r.status_code}')
data = r.json()
print(json.dumps(data, indent=2, ensure_ascii=False))
