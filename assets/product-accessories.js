/**
 * product-accessories.js
 * Handles selection and total calculation for product accessories.
 */

document.addEventListener('DOMContentLoaded', function() {
  const container = document.querySelector('.product-accessories-container');
  if (!container) return;

  const checkboxes = container.querySelectorAll('.accessory-input');
  const totalDisplay = container.querySelector('.total-price-display');
  const totalSection = container.querySelector('.product-accessories-total');
  
  function formatMoney(cents) {
    // Basic money formatter - in a real theme we'd use Shopify.formatMoney
    return '$' + (cents / 100).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
  }

  function updateTotalPrice() {
    let basePrice = parseInt(totalDisplay.dataset.basePrice);
    let extraPrice = 0;
    let selectedCount = 0;

    checkboxes.forEach(checkbox => {
      if (checkbox.checked) {
        extraPrice += parseInt(checkbox.dataset.price);
        selectedCount++;
      }
    });

    if (selectedCount > 0) {
      totalSection.style.display = 'block';
      totalDisplay.textContent = formatMoney(basePrice + extraPrice);
    } else {
      totalSection.style.display = 'none';
    }
  }

  checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', updateTotalPrice);
  });

  // Intercept the main Add to Cart form
  const productForm = document.querySelector('form[action="/cart/add"]');
  if (productForm) {
    productForm.addEventListener('submit', function(e) {
      const selectedAccessories = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => ({
          id: cb.value,
          quantity: 1
        }));

      if (selectedAccessories.length > 0) {
        e.preventDefault();
        
        // Prepare items array for Shopify AJAX API
        const formData = new FormData(productForm);
        const mainId = formData.get('id');
        const mainQty = formData.get('quantity') || 1;

        const items = [
          { id: mainId, quantity: parseInt(mainQty) },
          ...selectedAccessories
        ];

        fetch('/cart/add.js', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items: items })
        })
        .then(response => response.json())
        .then(data => {
          // Redirect to cart or show success message
          window.location.href = '/cart';
        })
        .catch(error => {
          console.error('Error adding to cart:', error);
          // Fallback: submit original form if AJAX fails
          productForm.submit();
        });
      }
    });
  }
});
