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

    checkboxes.forEach(input => {
      if (input.checked) {
        extraPrice += parseInt(input.dataset.price);
      }
    });

    totalDisplay.textContent = formatMoney(basePrice + extraPrice);
  }

  checkboxes.forEach(input => {
    input.addEventListener('change', updateTotalPrice);
  });

  // Intercept the main Add to Cart form
  const productForm = document.querySelector('form[action="/cart/add"]');
  if (productForm) {
    productForm.addEventListener('submit', function(e) {
      const selectedInputs = Array.from(checkboxes).filter(input => input.checked);
      
      if (selectedInputs.length > 0) {
        e.preventDefault();
        
        const formData = new FormData(productForm);
        const mainId = formData.get('id');
        const mainQty = parseInt(formData.get('quantity') || 1);

        const items = [{ id: mainId, quantity: mainQty }];

        selectedInputs.forEach(input => {
          items.push({
            id: input.value,
            quantity: mainQty // Normalmente se agrega uno por cada producto principal
          });
        });

        fetch('/cart/add.js', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items: items })
        })
        .then(response => {
          if (!response.ok) throw new Error('Network response was not ok');
          return response.json();
        })
        .then(() => {
          window.location.href = '/cart';
        })
        .catch(error => {
          console.error('Error adding to cart:', error);
          productForm.submit();
        });
      }
    });
  }
});
