/**
 * product-accessories.js
 * Handles grouped accessory selection, real-time price calculation,
 * and AJAX cart submission for Shopify product configurator.
 * 
 * Improvements v2:
 * - Fixed missing totalSection reference (element was renamed in HTML).
 * - Uses Shopify.formatMoney when available, falls back to CLP format.
 * - Adds visual 'selected' state to accessory items.
 * - Price always updates on any change (radio or checkbox).
 * - Handles the case where NO accessories are selected (standard form submit).
 * - Prevents double-submit on slow connections.
 */

document.addEventListener('DOMContentLoaded', function () {
  const container = document.querySelector('.product-accessories-container');
  if (!container) return;

  const inputs = container.querySelectorAll('.accessory-input');
  const totalDisplay = container.querySelector('.total-price-display');
  const summaryBox = container.querySelector('.product-accessories-summary');

  // ── Formatting ────────────────────────────────────────────────────────────
  // Shopify stores prices in cents. Use Shopify.formatMoney if available.
  // Fallback formats to Chilean peso (CLP): $ 13.000
  function formatMoney(cents) {
    if (window.Shopify && window.Shopify.formatMoney) {
      return Shopify.formatMoney(cents, window.Shopify.money_format || '${{amount_no_decimals}}');
    }
    const amount = Math.round(cents / 100);
    return '$\u00a0' + amount.toLocaleString('es-CL');
  }

  // ── Price Calculation ─────────────────────────────────────────────────────
  function updateTotalPrice() {
    const basePrice = parseInt(totalDisplay.dataset.basePrice, 10) || 0;
    let extraPrice = 0;

    inputs.forEach(input => {
      if (input.checked) {
        extraPrice += parseInt(input.dataset.price, 10) || 0;
      }
    });

    totalDisplay.textContent = formatMoney(basePrice + extraPrice);

    // Show the summary box only when there's something to add
    if (summaryBox) {
      summaryBox.style.display = extraPrice > 0 ? 'block' : '';
    }
  }

  // ── Visual State ──────────────────────────────────────────────────────────
  function updateSelectedState(changedInput) {
    const group = changedInput.dataset.group;

    // For radios: clear 'selected' state from all siblings in the same group
    if (changedInput.type === 'radio') {
      inputs.forEach(input => {
        if (input.dataset.group === group) {
          input.closest('.product-accessory-item').classList.remove('is-selected');
        }
      });
    }

    if (changedInput.checked) {
      changedInput.closest('.product-accessory-item').classList.add('is-selected');
    } else {
      changedInput.closest('.product-accessory-item').classList.remove('is-selected');
    }
  }

  inputs.forEach(input => {
    input.addEventListener('change', function () {
      updateSelectedState(this);
      updateTotalPrice();
    });
  });

  // ── AJAX Add to Cart ──────────────────────────────────────────────────────
  const productForm = document.querySelector('form[action="/cart/add"]');
  if (!productForm) return;

  let isSubmitting = false;

  productForm.addEventListener('submit', function (e) {
    const selectedInputs = Array.from(inputs).filter(i => i.checked);

    // If no accessories are selected, let the form submit normally
    if (selectedInputs.length === 0) return;

    e.preventDefault();
    if (isSubmitting) return;
    isSubmitting = true;

    const submitBtn = productForm.querySelector('[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Agregando...';
    }

    const formData = new FormData(productForm);
    const mainId = formData.get('id');
    const mainQty = parseInt(formData.get('quantity') || 1, 10);

    const items = [{ id: mainId, quantity: mainQty }];

    selectedInputs.forEach(input => {
      items.push({ id: input.value, quantity: 1 });
    });

    fetch('/cart/add.js', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items })
    })
      .then(response => {
        if (!response.ok) throw new Error(`Cart error: ${response.status}`);
        return response.json();
      })
      .then(() => {
        window.location.href = '/cart';
      })
      .catch(error => {
        console.error('[product-accessories] Error adding to cart:', error);
        isSubmitting = false;
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Agregar al carrito';
        }
        // Show user-friendly error
        const msg = container.querySelector('.accessories-error');
        if (msg) msg.style.display = 'block';
      });
  });
});
