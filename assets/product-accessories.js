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

  const checkboxes = container.querySelectorAll('.accessory-input');
  const selects = container.querySelectorAll('.accessory-select');
  const totalDisplay = container.querySelector('.total-price-display');
  const summaryBox = container.querySelector('.product-accessories-summary');

  // ── Formatting ────────────────────────────────────────────────────────────
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

    // Sum checkboxes
    checkboxes.forEach(input => {
      if (input.checked) {
        extraPrice += parseInt(input.dataset.price, 10) || 0;
      }
    });

    // Sum selects
    selects.forEach(select => {
      const selectedOption = select.options[select.selectedIndex];
      if (selectedOption && selectedOption.value !== "") {
        extraPrice += parseInt(selectedOption.dataset.price, 10) || 0;
      }
    });

    totalDisplay.textContent = formatMoney(basePrice + extraPrice);

    if (summaryBox) {
      summaryBox.style.display = extraPrice > 0 ? 'block' : '';
    }
  }

  // ── Event Listeners ───────────────────────────────────────────────────────
  checkboxes.forEach(input => {
    input.addEventListener('change', function () {
      // Visual feedback for checkboxes
      if (this.checked) {
        this.closest('.product-accessory-item').classList.add('is-selected');
      } else {
        this.closest('.product-accessory-item').classList.remove('is-selected');
      }
      updateTotalPrice();
    });
  });

  selects.forEach(select => {
    select.addEventListener('change', updateTotalPrice);
  });

  // ── AJAX Add to Cart ──────────────────────────────────────────────────────
  const productForm = document.querySelector('form[action="/cart/add"]');
  if (!productForm) return;

  let isSubmitting = false;

  productForm.addEventListener('submit', function (e) {
    const selectedVariants = [];
    
    // Get checked checkboxes
    checkboxes.forEach(i => { if (i.checked) selectedVariants.push(i.value); });
    // Get selected options from selects
    selects.forEach(s => { 
      if (s.value !== "") selectedVariants.push(s.value); 
    });

    if (selectedVariants.length === 0) return;

    e.preventDefault();
    if (isSubmitting) return;
    isSubmitting = true;

    const submitBtn = productForm.querySelector('[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Agregando...';
    }

    const formData = new FormData(productForm);
    const mainId = formData.get('id');
    const mainQty = parseInt(formData.get('quantity') || 1, 10);

    const items = [{ id: mainId, quantity: mainQty }];
    selectedVariants.forEach(id => {
      items.push({ id: id, quantity: 1 });
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
        console.error('[product-accessories] Error:', error);
        isSubmitting = false;
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Agregar al carrito';
        }
        const msg = container.querySelector('.accessories-error');
        if (msg) msg.style.display = 'block';
      });
  });
});
