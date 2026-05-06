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

### 2. Upload Files
- Upload `snippets/product-accessories.liquid` to your theme's `snippets` folder.
- Upload `assets/product-accessories.js` to your theme's `assets` folder.

### 3. Integrate into Product Template
Find your main product section (usually `sections/main-product.liquid` or `snippets/product-form.liquid`).
Place the following code where you want the accessories to appear (usually above the "Add to Cart" button):

```liquid
{% render 'product-accessories', product: product %}
```

### 4. How it works
- The snippet checks for products listed in the `custom.accessories` metafield.
- It displays them with checkboxes.
- When the "Add to Cart" button is clicked, the script intercepts the event and uses the Shopify AJAX API to add both the main product and all selected accessories at once.
