function getCSRFToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Currency formatting function - matches your Django format_currency function
function formatCurrency(amount) {
  // Get currency settings from Django template variables (set in HTML)
  const currencySymbol = window.CURRENCY_SYMBOL || 'P';
  const useThousandSeparator = window.THOUSAND_SEPARATOR !== false;
  const decimalPlaces = window.DECIMAL_PLACES || 2;
  
  // Format the number with decimal places
  let formattedAmount = parseFloat(amount).toFixed(decimalPlaces);
  
  // Add thousand separator if enabled
  if (useThousandSeparator) {
    const parts = formattedAmount.split('.');
    parts[0] = parseInt(parts[0]).toLocaleString();
    formattedAmount = parts.join('.');
  }
  
  return formattedAmount;
}

// Simple formatting function for input fields (no decimal places forced)
function formatInputCurrency(amount) {
  const useThousandSeparator = window.THOUSAND_SEPARATOR !== false;
  
  if (!useThousandSeparator) {
    return amount.toString();
  }
  
  // Split by decimal point
  const parts = amount.toString().split('.');
  
  // Format the integer part with thousand separators
  parts[0] = parseInt(parts[0]).toLocaleString();
  
  // Rejoin with decimal part if it exists
  return parts.join('.');
}

function setCursorPosition(input, position) {
  input.setSelectionRange(position, position);
}

// Function to format all product prices on the page
function formatProductPrices() {
  document.querySelectorAll('.product-card').forEach(card => {
    const priceElement = card.querySelector('.card-body span:first-child');
    if (priceElement) {
      const price = parseFloat(card.dataset.price);
      const currencySymbol = window.CURRENCY_SYMBOL || 'P';
      priceElement.textContent = `${currencySymbol}${formatCurrency(price)}`;
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  let cart = [];
  const defaultTax = 8; // Hardcode tax rate for simplicity

  // Unified API configuration
  const API_BASE_URL = '/api/sales/';
  console.log('Using API base URL:', API_BASE_URL);

  // Format product prices on page load
  formatProductPrices();

  document.getElementById('productSearch').addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    document.querySelectorAll('.product-card').forEach(card => {
      const name = card.dataset.name.toLowerCase();
      card.style.display = name.includes(searchTerm) ? 'block' : 'none';
    });
  });

  document.querySelectorAll('.product-card').forEach(card => {
    card.addEventListener('click', () => {
      const product = {
        id: card.dataset.id,
        name: card.dataset.name,
        price: parseFloat(card.dataset.price),
        stock: parseInt(card.dataset.stock)
      };

      if (product.stock < 1) {
        showAlert('This product is out of stock!', 'danger');
        return;
      }

      const existing = cart.find(item => item.id === product.id);
      if (existing) {
        if (existing.quantity >= product.stock) {
          showAlert('Cannot exceed available stock', 'warning');
          return;
        }
        existing.quantity++;
      } else {
        cart.push({ ...product, quantity: 1 });
      }

      updateCartDisplay();
      updateProductStockDisplay(product.id, -1);
      showAlert(`Added ${product.name} to cart`, 'success', 1000);
    });
  });

  window.showAlert = (message, type = 'info', duration = 3000) => {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed bottom-0 end-0 m-3`;
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    
    if (duration) {
      setTimeout(() => {
        alertDiv.remove();
      }, duration);
    }
  };

  function updateCartDisplay() {
    const cartDiv = document.getElementById('cartItems');
    const currencySymbol = window.CURRENCY_SYMBOL || 'P';
    
    cartDiv.innerHTML = cart.map((item, index) => `
      <div class="d-flex justify-content-between align-items-center mb-2">
        <div>
          <span class="fw-bold">${item.name}</span><br>
          <small>${currencySymbol}${formatCurrency(item.price)} x ${item.quantity}</small>
        </div>
        <div>
          <button class="btn btn-sm btn-outline-secondary" 
                  onclick="adjustQuantity(${index}, -1)">−</button>
          <span class="mx-2">${item.quantity}</span>
          <button class="btn btn-sm btn-outline-secondary" 
                  onclick="adjustQuantity(${index}, 1)">+</button>
          <button class="btn btn-sm btn-danger ms-2" 
                  onclick="removeItem(${index})">×</button>
        </div>
      </div>
    `).join('');

    if (cart.length === 0) {
      cartDiv.innerHTML = '<div class="text-center text-muted p-3">Cart is empty</div>';
    }

    updateTotals();
    
    const paymentButton = document.getElementById('processPaymentBtn');
    if (paymentButton) {
      paymentButton.disabled = cart.length === 0;
    }
  }

  window.adjustQuantity = (index, delta) => {
    const item = cart[index];
    const newQuantity = item.quantity + delta;

    if (newQuantity < 1) {
      window.removeItem(index);
      return;
    }

    if (newQuantity > item.stock) {
      showAlert('Cannot exceed available stock', 'warning');
      return;
    }

    item.quantity = newQuantity;
    updateProductStockDisplay(item.id, -delta);
    updateCartDisplay();
  };

  window.removeItem = (index) => {
    const item = cart[index];
    updateProductStockDisplay(item.id, item.quantity);
    cart.splice(index, 1);
    updateCartDisplay();
  };

  function updateProductStockDisplay(productId, quantityDelta) {
    const card = document.querySelector(`.product-card[data-id="${productId}"]`);
    if (card) {
      const stockElement = card.querySelector('.badge');
      let currentStock = parseInt(card.dataset.stock);
      currentStock -= quantityDelta;
      card.dataset.stock = currentStock;
      stockElement.textContent = `Stock: ${currentStock}`;
      stockElement.className = currentStock > 0 ? 'badge bg-success' : 'badge bg-danger';
    }
  }

  window.updateTotals = () => {
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const discountPercent = parseFloat(document.getElementById('discountInput').value) || 0;
    const discountAmount = subtotal * (discountPercent / 100);
    const taxAmount = (subtotal - discountAmount) * (defaultTax / 100);
    const total = subtotal - discountAmount + taxAmount;

    // Use formatCurrency function for proper formatting
    document.getElementById('subtotal').textContent = formatCurrency(subtotal);
    document.getElementById('discountAmount').textContent = formatCurrency(discountAmount);
    document.getElementById('taxAmount').textContent = formatCurrency(taxAmount);
    document.getElementById('totalAmount').textContent = formatCurrency(total);
    
    calculateChange();
  };

  // Format amount paid input as user types
  window.formatAmountPaidInput = (input) => {
    let value = input.value.replace(/,/g, ''); // Remove existing commas
    if (value && !isNaN(value)) {
      const formatted = formatCurrency(parseFloat(value));
      input.value = formatted;
    }
  };
  
  window.calculateChange = () => {
    const totalText = document.getElementById('totalAmount').textContent;
    // Remove commas and parse the total
    const total = parseFloat(totalText.replace(/,/g, ''));
    const amountPaid = parseFloat(document.getElementById('amountPaidInput').value.replace(/,/g, '')) || 0;
    const change = amountPaid - total;
    
    const changeElement = document.getElementById('changeAmount');
    if (changeElement) {
      changeElement.textContent = formatCurrency(change);
      
      const changeRow = changeElement.closest('.change-row');
      if (changeRow) {
        changeRow.classList.toggle('text-danger', change < 0);
        changeRow.classList.toggle('text-success', change >= 0);
      }
    }
    
    const paymentButton = document.getElementById('processPaymentBtn');
    if (paymentButton) {
      paymentButton.disabled = cart.length === 0 || (amountPaid < total && amountPaid > 0);
    }
  };

  window.clearCart = () => {
    if (cart.length === 0) return;
    if (!confirm('Are you sure you want to clear the cart?')) return;
    
    cart.forEach(item => updateProductStockDisplay(item.id, item.quantity));
    cart = [];
    updateCartDisplay();
  };

  window.completeOrder = async () => {
    const paymentBtn = document.getElementById('processPaymentBtn');
    const originalBtnText = paymentBtn.innerHTML;
    paymentBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing...';
    paymentBtn.disabled = true;

    try {
      // Prepare order data
      const orderData = {
        items: cart.map(item => ({
          product: item.id,
          quantity: item.quantity,
          price: item.price
        })),
        tax_rate: defaultTax,
        discount: parseFloat(document.getElementById('discountInput').value) || 0,
        payment_method: document.getElementById('paymentMethod').value,
        amount_paid: parseFloat(document.getElementById('amountPaidInput').value.replace(/,/g, '')) || 0,
      };

      // Create headers for session-based authentication
      const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      };

      console.log('Sending order data:', orderData);

      // Create order using session authentication
      const createResponse = await fetch(`${API_BASE_URL}orders/`, {
        method: 'POST',
        headers: headers,
        credentials: 'same-origin',  // Use same-origin for session auth
        body: JSON.stringify(orderData)
      });

      console.log('Create order response status:', createResponse.status);

      if (!createResponse.ok) {
        const errorData = await createResponse.json().catch(() => null);
        const errorText = errorData ? JSON.stringify(errorData) : await createResponse.text();
        console.error('Order creation failed:', errorText);
        throw new Error(`Order creation failed: ${createResponse.status} - ${errorText}`);
      }

      const order = await createResponse.json();
      console.log('Order created successfully:', order);
      
      // Generate receipt - use the same headers
      const receiptUrl = `${API_BASE_URL}orders/${order.id}/receipt/?format=html`;
      const receiptResponse = await fetch(receiptUrl, {
        headers: headers,
        credentials: 'same-origin'  // Use same-origin for session auth
      });
      
      if (!receiptResponse.ok) {
        const errorText = await receiptResponse.text();
        console.error('Receipt generation failed:', errorText);
        throw new Error(`Receipt generation failed: ${receiptResponse.status} - ${errorText}`);
      }
      
      const receiptHTML = await receiptResponse.text();
      document.getElementById('receiptContent').innerHTML = receiptHTML;
      
      // Show receipt modal
      new bootstrap.Modal(document.getElementById('receiptModal')).show();
      
      // Reset cart and form
      cart = [];
      updateCartDisplay();
      document.getElementById('amountPaidInput').value = '';
      document.getElementById('discountInput').value = '';
      
      // Reload product info to get updated stock levels
      await reloadProductInfo();

    } catch (error) {
      console.error('Order processing error:', error);
      showAlert(`Error: ${error.message}`, 'danger');
    } finally {
      paymentBtn.innerHTML = originalBtnText;
      paymentBtn.disabled = cart.length === 0;
    }
  };
  
  async function reloadProductInfo() {
    try {
      const response = await fetch('/api/products/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
      });
      
      if (response.ok) {
        const products = await response.json();
        
        products.forEach(product => {
          const card = document.querySelector(`.product-card[data-id="${product.id}"]`);
          if (card) {
            card.dataset.stock = product.stock;
            card.dataset.price = product.price; // Update price data as well
            
            // Update stock display
            const stockElement = card.querySelector('.badge');
            if (stockElement) {
              stockElement.textContent = `Stock: ${product.stock}`;
              stockElement.className = product.stock > 0 ? 'badge bg-success' : 'badge bg-danger';
            }
            
            // Update price display with proper formatting
            const priceElement = card.querySelector('.card-body span:first-child');
            if (priceElement) {
              const currencySymbol = window.CURRENCY_SYMBOL || 'P';
              priceElement.textContent = `${currencySymbol}${formatCurrency(product.price)}`;
            }
          }
        });
        
        console.log('Product info reloaded successfully');
      } else {
        console.error('Failed to reload product data:', response.status);
        showAlert('Failed to update product info. Please refresh the page.', 'warning');
      }
    } catch (error) {
      console.error('Error reloading product data:', error);
      showAlert('Error updating product data. Please refresh the page.', 'danger');
    }
  }

  window.printReceipt = () => {
    const receiptContent = document.getElementById('receiptContent').innerHTML;
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Receipt</title>
          <style>
            body { font-family: monospace; }
            pre { white-space: pre-wrap; }
          </style>
        </head>
        <body>
          ${receiptContent}
          <script>
            window.onload = function() {
              window.print();
              setTimeout(function() { window.close(); }, 500);
            };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  // Prevent form submission for payment button with double-click protection
  const processPaymentBtn = document.getElementById('processPaymentBtn');
  if (processPaymentBtn) {
    let isProcessing = false;
    
    processPaymentBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      if (isProcessing || processPaymentBtn.disabled) {
        console.log('Order already processing or button disabled, ignoring click');
        return;
      }
      
      console.log('Payment button clicked - starting order process');
      
      isProcessing = true;
      
      try {
        await window.completeOrder();
      } catch (error) {
        console.error('Error in payment button handler:', error);
        showAlert(`Order failed: ${error.message}`, 'danger');
      } finally {
        // Reset processing flag after a short delay
        setTimeout(() => {
          isProcessing = false;
          console.log('Payment button protection reset');
        }, 2000);
      }
    });
  }

  // Initialize other event listeners - FIXED AMOUNT PAID INPUT
  if (document.getElementById('amountPaidInput')) {
    const amountInput = document.getElementById('amountPaidInput');
    let isFormatting = false;

    amountInput.addEventListener('input', (e) => {
      if (isFormatting) return;
      
      const input = e.target;
      const cursorPosition = input.selectionStart;
      let value = input.value.replace(/,/g, ''); // Remove existing commas
      
      // Allow only numbers and one decimal point
      if (!/^\d*\.?\d*$/.test(value)) {
        value = value.slice(0, -1);
      }
      
      // Apply thousand separators in real-time if there's a valid number
      if (value && !isNaN(value) && value.trim() !== '') {
        isFormatting = true;
        
        // Split by decimal point
        const parts = value.split('.');
        const integerPart = parts[0];
        
        // Add thousand separators to integer part if it has 4+ digits
        if (integerPart.length >= 4) {
          const formattedInteger = parseInt(integerPart).toLocaleString();
          const formattedValue = parts.length > 1 ? `${formattedInteger}.${parts[1]}` : formattedInteger;
          
          input.value = formattedValue;
          
          // Adjust cursor position
          const addedCommas = formattedValue.length - value.length;
          const newCursorPos = Math.max(0, cursorPosition + addedCommas);
          setTimeout(() => {
            input.setSelectionRange(newCursorPos, newCursorPos);
            isFormatting = false;
          }, 0);
        } else {
          input.value = value;
          isFormatting = false;
        }
      } else {
        input.value = value;
      }
      
      calculateChange();
    });

    // Clean up formatting on blur if needed
    amountInput.addEventListener('blur', (e) => {
      const input = e.target;
      let value = input.value.replace(/,/g, '');
      
      if (value && !isNaN(value) && value.trim() !== '') {
        const num = parseFloat(value);
        input.value = formatInputCurrency(num);
      }
      
      calculateChange();
    });
  }

  if (document.getElementById('discountInput')) {
    document.getElementById('discountInput').addEventListener('input', updateTotals);
  }

  // Initialize display
  updateCartDisplay();
});