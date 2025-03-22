// Main JavaScript for FarmConnect

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Product quantity increment/decrement functionality
    const quantityInputs = document.querySelectorAll('.quantity-input');
    if (quantityInputs.length > 0) {
        quantityInputs.forEach(input => {
            const decrementBtn = input.previousElementSibling;
            const incrementBtn = input.nextElementSibling;
            
            if (decrementBtn && incrementBtn) {
                decrementBtn.addEventListener('click', () => {
                    let value = parseInt(input.value);
                    if (value > 1) {
                        input.value = value - 1;
                        triggerChangeEvent(input);
                    }
                });
                
                incrementBtn.addEventListener('click', () => {
                    let value = parseInt(input.value);
                    let max = parseInt(input.getAttribute('max') || 100);
                    if (value < max) {
                        input.value = value + 1;
                        triggerChangeEvent(input);
                    }
                });
            }
        });
    }
    
    // Helper function to trigger change event
    function triggerChangeEvent(element) {
        const event = new Event('change', { bubbles: true });
        element.dispatchEvent(event);
    }
    
    // Dynamic price calculation for order form
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        const quantityInput = document.getElementById('id_quantity');
        const unitPrice = document.getElementById('unit_price');
        const totalPrice = document.getElementById('total_price');
        
        if (quantityInput && unitPrice && totalPrice) {
            const price = parseFloat(unitPrice.getAttribute('data-price'));
            
            quantityInput.addEventListener('change', () => {
                const quantity = parseInt(quantityInput.value);
                const total = (price * quantity).toFixed(2);
                totalPrice.textContent = total;
            });
        }
    }
    
    // Fade out alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 5000);
    }
    
    // Enable image preview for file inputs
    const imageInputs = document.querySelectorAll('input[type="file"][data-preview]');
    if (imageInputs.length > 0) {
        imageInputs.forEach(input => {
            const previewEl = document.getElementById(input.getAttribute('data-preview'));
            if (previewEl) {
                input.addEventListener('change', () => {
                    if (input.files && input.files[0]) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            previewEl.src = e.target.result;
                        };
                        reader.readAsDataURL(input.files[0]);
                    }
                });
            }
        });
    }
    
    // Enhance Google Translate functionality
    // Fix the Google Translate attribution bar that sometimes appears
    var fixGoogleTranslate = function() {
        // Fix body position if Google Translate changed it
        if (document.body.style.top) {
            document.body.style.top = '';
        }
        
        // Hide Google Translate frame if visible
        var iframe = document.querySelector('.goog-te-banner-frame');
        if (iframe) {
            iframe.style.display = 'none';
        }
        
        // Restore scrolling if Google Translate changed it
        document.documentElement.style.overflow = '';
        document.body.style.overflow = '';
    };
    
    // Run initially and whenever window is resized (which can trigger Google Translate issues)
    fixGoogleTranslate();
    window.addEventListener('resize', fixGoogleTranslate);
    
    // Run periodically to catch any changes Google Translate might make
    setInterval(fixGoogleTranslate, 1500);
    
    // Handle cookie for remembering selected language
    if (localStorage.getItem('googtrans')) {
        var storedLang = localStorage.getItem('googtrans');
        var cookieLang = getCookie('googtrans');
        
        // Sync cookie with localStorage if they don't match
        if (storedLang && (!cookieLang || cookieLang !== storedLang)) {
            document.cookie = 'googtrans=' + storedLang + '; path=/; domain=.' + window.location.hostname;
        }
    }
    
    // Helper function to get cookie value
    function getCookie(name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length == 2) return parts.pop().split(";").shift();
    }
}); 