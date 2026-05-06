# Shopify Accessory Groups Feature

This repository contains a Liquid-based solution to add an "Accessory Group" selection to your Shopify product pages.

## Files included:
1. `snippets/product-accessories.liquid`: The UI component.
2. `assets/product-accessories.js`: Logic for price calculation and AJAX cart addition.

## Setup Instructions:

### 1. Create Metafield
In your Shopify Admin:
- Go to **Settings > Custom Data > Products**.
- Click **Add definition**.
- **Name**: `Accessories`
- **Namespace and key**: `custom.accessories`
- **Type**: `List of products` (Reference > Product > List of products).

### 2. Configurar Productos de Accesorios
Para cada accesorio (ej. "Patas Cromadas"):
- Créalo como un producto independiente.
- **Importante**: Asigna un **Product Type** (Tipo de producto) descriptivo (ej. `Patas`, `Brazos`, `Accesorios`).
- El sistema agrupará automáticamente los accesorios por este campo.
- **Lógica de selección**:
    - Si el tipo es `Accesorios` o `Extras`, el cliente puede seleccionar varios (Checkboxes).
    - Para cualquier otro tipo (ej. `Patas`), el sistema asume que es excluyente y usa Radio Buttons (solo uno por grupo).

### 3. Vincular con el Producto Principal
En el producto principal (ej. Silla), usa el metafield `custom.accessories` para seleccionar todos los productos que deben aparecer como opciones.

### 5. Migration Hub Dashboard
He creado una herramienta visual para ayudarte a gestionar todo el proceso:
- Abre el archivo `migration-hub.html` en tu navegador para ver el estado de la migración y acceder a las instrucciones interactivas.
