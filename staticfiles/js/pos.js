function getCSRFToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

document.addEventListener('DOMContentLoaded', () => {
  let cart = [];
  const defaultTax = 8; // Hardcode tax rate for simplicity

  // Unified API configuration
  const API_BASE_URL = '/api/sales/';
  console.log('Using API base URL:', API_BASE_URL);

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
    cartDiv.innerHTML = cart.map((item, index) => `
      <div class="d-flex justify-content-between align-items-center mb-2">
        <div>
          <span class="fw-bold">${item.name}</span><br>
          <small>$${item.price.toFixed(2)} x ${item.quantity}</small>
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

    document.getElementById('subtotal').textContent = subtotal.toFixed(2);
    document.getElementById('discountAmount').textContent = discountAmount.toFixed(2);
    document.getElementById('taxAmount').textContent = taxAmount.toFixed(2);
    document.getElementById('totalAmount').textContent = total.toFixed(2);
    
    calculateChange();
  };
  
  window.calculateChange = () => {
    const total = parseFloat(document.getElementById('totalAmount').textContent);
    const amountPaid = parseFloat(document.getElementById('amountPaidInput').value) || 0;
    const change = amountPaid - total;
    
    const changeElement = document.getElementById('changeAmount');
    if (changeElement) {
      changeElement.textContent = change.toFixed(2);
      
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
        amount_paid: parseFloat(document.getElementById('amountPaidInput').value) || 0,
      };

      // Create headers with authentication
      const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      };
      
      // Add JWT token if available
      const token = localStorage.getItem('token') || sessionStorage.getItem('token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Create order
      const createResponse = await fetch(`${API_BASE_URL}orders/`, {
        method: 'POST',
        headers: headers,
        credentials: 'include',  // Crucial for session-based auth
        body: JSON.stringify(orderData)
      });

      if (!createResponse.ok) {
        const errorText = await createResponse.text();
        throw new Error(`Order creation failed: ${createResponse.status} - ${errorText}`);
      }

      const order = await createResponse.json();
      
      // Generate receipt - use the same headers
      const receiptUrl = `${API_BASE_URL}orders/${order.id}/receipt/?format=html`;
      const receiptResponse = await fetch(receiptUrl, {
        headers: headers,
        credentials: 'include'  // Crucial for session-based auth
      });
      
      if (!receiptResponse.ok) {
        const errorText = await receiptResponse.text();
        throw new Error(`Receipt generation failed: ${receiptResponse.status} - ${errorText}`);
      }
      
      const receiptHTML = await receiptResponse.text();
      document.getElementById('receiptContent').innerHTML = receiptHTML;
      
      // Show receipt modal
      new bootstrap.Modal(document.getElementById('receiptModal')).show();
      
      // Reset cart
      cart = [];
      updateCartDisplay();
      document.getElementById('amountPaidInput').value = '';

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
            const stockElement = card.querySelector('.badge');
            if (stockElement) {
              stockElement.textContent = `Stock: ${product.stock}`;
              stockElement.className = product.stock > 0 ? 'badge bg-success' : 'badge bg-danger';
            }
          }
        });
      } else {
        console.error('Failed to reload product data');
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
    let processingTimeout = null;
    
    processPaymentBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      // Strong double-click protection
      if (isProcessing || processPaymentBtn.disabled) {
        console.log('Order already processing or button disabled, ignoring click');
        return;
      }
      
      console.log('Payment button clicked - starting order process');
      
      // Immediately set processing state and disable button
      isProcessing = true;
      processPaymentBtn.disabled = true;
      
      // Clear any existing timeout
      if (processingTimeout) {
        clearTimeout(processingTimeout);
      }
      
      try {
        await window.completeOrder();
      } catch (error) {
        console.error('Error in payment button handler:', error);
        showAlert(`Order failed: ${error.message}`, 'danger');
      } finally {
        // Reset processing state after a delay
        processingTimeout = setTimeout(() => {
          isProcessing = false;
          // Only re-enable if cart has items and no error state
          if (cart && cart.length > 0 && !processPaymentBtn.innerHTML.includes('Processing')) {
            processPaymentBtn.disabled = false;
          }
          console.log('Payment button protection reset, cart length:', cart ? cart.length : 0);
        }, 3000); // Increased to 3 seconds
      }
    });
  }

  // Initialize other event listeners
  if (document.getElementById('amountPaidInput')) {
    document.getElementById('amountPaidInput').addEventListener('input', calculateChange);
  }

  updateCartDisplay();
  document.getElementById('discountInput').addEventListener('input', updateTotals);
});

window.testReceiptUrl = async (orderId) => {
  console.log('=== TESTING RECEIPT URL ===');
  const testUrls = [
    `/api/orders/${orderId}/receipt/?format=html`,
    `/api/orders/${orderId}/receipt/`
  ];
  
  for (const url of testUrls) {
    console.log(`Testing URL: ${url}`);
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'Accept': 'text/html, */*'
        },
        credentials: 'same-origin'
      });
      
      console.log(`  Status: ${response.status}`);
      console.log(`  Headers:`, [...response.headers.entries()]);
      
      if (response.ok) {
        const content = await response.text();
        console.log(`  Content length: ${content.length}`);
        console.log(`  Content preview: ${content.substring(0, 200)}`);
        console.log(`✅ URL ${url} works!`);
        return url;
      } else {
        const errorText = await response.text();
        console.log(`  Error: ${errorText}`);
      }
    } catch (error) {
      console.log(`  Exception: ${error.message}`);
    }
  }
  
  console.log('❌ No working URLs found');
  return null;
};