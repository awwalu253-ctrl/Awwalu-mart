// ============================================
// API BASE URL (auto-detect)
// ============================================
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api'
    : '/api';

// ============================================
// MAINTENANCE MODE CHECK
// ============================================
async function checkMaintenance() {
    try {
        const res = await fetch(`${API_BASE}/maintenance`);
        const data = await res.json();
        if (data.maintenance === true) {
            // Show maintenance page
            document.body.innerHTML = `
                <div style="display:flex; align-items:center; justify-content:center; min-height:100vh; background:#faf8f5; text-align:center; padding:20px; flex-direction:column; font-family: 'Inter', sans-serif;">
                    <i class="fas fa-tools" style="font-size:64px; color:#b8860b; margin-bottom:20px;"></i>
                    <h1 style="font-size:32px; color:#2d2a24;">Under Maintenance</h1>
                    <p style="color:#8a8078; max-width:400px; margin:0 auto;">We're currently updating our kitchen collection. Please check back soon!</p>
                    <p style="color:#b5aaa2; font-size:14px; margin-top:12px;">🕒 Estimated time: 30 minutes</p>
                </div>
            `;
            return true; // Maintenance is on
        }
        return false; // Maintenance is off
    } catch (error) {
        console.log('Maintenance check failed:', error);
        return false;
    }
}

// ============================================
// NAVBAR & FOOTER
// ============================================
function loadNavbar() {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;

    const cartItems = JSON.parse(localStorage.getItem('awwalumart-cart') || '[]');
    const totalItems = cartItems.reduce((sum, item) => sum + (item.quantity || 1), 0);

    // === CHANGE THIS TO YOUR CLOUDINARY URL ===
    const logoUrl = 'https://res.cloudinary.com/your-cloud-name/image/upload/your-logo.png';

    navbar.innerHTML = `
        <div class="container">
            <div class="navbar-left">
                <a href="index.html">
                    <img src="${logoUrl}" alt="Awwalu Kitchen Vault" class="logo" />
                </a>
            </div>
            <div class="navbar-right">
                <div class="nav-links">
                    <a href="index.html" class="${window.location.pathname.includes('index') ? 'active' : ''}">Home</a>
                    <a href="products.html" class="${window.location.pathname.includes('products') ? 'active' : ''}">Products</a>
                    <a href="bundles.html" class="${window.location.pathname.includes('bundles') ? 'active' : ''}">Bundles</a>
                    <a href="about.html" class="${window.location.pathname.includes('about') ? 'active' : ''}">About</a>
                    <a href="contact.html" class="${window.location.pathname.includes('contact') ? 'active' : ''}">Contact</a>
                </div>
                <span class="cart-icon" onclick="window.location.href='cart.html'">
                    <i class="fas fa-shopping-cart"></i>
                    <span class="cart-badge" id="cartBadgeNav">${totalItems}</span>
                </span>
                <button class="hamburger" onclick="toggleMobileMenu()">
                    <i class="fas fa-bars"></i>
                </button>
            </div>
        </div>
        <div class="mobile-menu" id="mobileMenu">
            <a href="index.html">Home</a>
            <a href="products.html">Products</a>
            <a href="bundles.html">Bundles</a>
            <a href="about.html">About</a>
            <a href="contact.html">Contact</a>
            <a href="cart.html">Cart (<span id="mobileCartCount">${totalItems}</span>)</a>
        </div>
    `;
    updateCartBadge();
}

function loadFooter() {
    const footer = document.getElementById('footer');
    if (!footer) return;
    
    // === CHANGE THIS TO YOUR CLOUDINARY URL ===
    const logoUrl = 'https://res.cloudinary.com/your-cloud-name/image/upload/your-logo.png';
    
    footer.innerHTML = `
        <div class="container">
            <img src="${logoUrl}" alt="Awwalu Kitchen Vault" style="height:48px; margin-bottom:12px;" />
            <p>&copy; 2026 Awwalu Kitchen Vault. All rights reserved.</p>
            <p class="small">Premium kitchen appliances, cookware, and utensils.</p>
        </div>
    `;
}

function toggleMobileMenu() {
    document.getElementById('mobileMenu').classList.toggle('open');
}

// ============================================
// CART MANAGEMENT (with quantities)
// ============================================
function getCart() {
    return JSON.parse(localStorage.getItem('awwalumart-cart') || '[]');
}

function saveCart(cart) {
    localStorage.setItem('awwalumart-cart', JSON.stringify(cart));
    updateCartBadge();
}

function updateCartBadge() {
    const cart = getCart();
    const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
    document.querySelectorAll('.cart-badge').forEach(el => {
        el.textContent = totalItems;
        el.classList.toggle('show', totalItems > 0);
    });
    const mobileCount = document.getElementById('mobileCartCount');
    if (mobileCount) mobileCount.textContent = totalItems;
}

function addToCart(product) {
    let cart = getCart();
    const existing = cart.find(p => p.id === product.id);
    if (existing) {
        existing.quantity = (existing.quantity || 1) + 1;
    } else {
        cart.push({ ...product, quantity: 1 });
    }
    saveCart(cart);
    showToast(`✅ ${product.name} added to cart!`);
}

function removeFromCart(productId) {
    let cart = getCart();
    const index = cart.findIndex(p => p.id === productId);
    if (index !== -1) {
        const item = cart[index];
        if (item.quantity > 1) {
            item.quantity--;
        } else {
            cart.splice(index, 1);
        }
        saveCart(cart);
        if (typeof renderCart === 'function') renderCart();
    }
}

function deleteItem(productId) {
    let cart = getCart();
    cart = cart.filter(p => p.id !== productId);
    saveCart(cart);
    if (typeof renderCart === 'function') renderCart();
}

function clearCart() {
    saveCart([]);
    if (typeof renderCart === 'function') renderCart();
}

function getCartTotal() {
    const cart = getCart();
    return cart.reduce((sum, p) => {
        const price = parseFloat(p.price.replace(/[^0-9.]/g, '') || '0');
        return sum + price * (p.quantity || 1);
    }, 0);
}

// ============================================
// TOAST NOTIFICATION
// ============================================
function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// PRODUCTS API
// ============================================
let allProducts = [];

async function fetchProducts() {
    try {
        const res = await fetch(`${API_BASE}/products`);
        if (!res.ok) throw new Error('Network error');
        const data = await res.json();
        allProducts = data;
        return data;
    } catch (error) {
        console.error('Error fetching products:', error);
        showToast('Failed to load products. Is the backend running?');
        return [];
    }
}

// ============================================
// HOMEPAGE: CATEGORIES (KITCHEN-ONLY)
// ============================================
function loadCategories() {
    const grid = document.getElementById('categoriesGrid');
    if (!grid) return;
    const categories = [
        { name: 'Cookware', icon: 'fa-pot-food', cls: 'cookware' },
        { name: 'Bakeware', icon: 'fa-bread-slice', cls: 'bakeware' },
        { name: 'Utensils', icon: 'fa-utensils', cls: 'utensils' },
        { name: 'Appliances', icon: 'fa-blender', cls: 'appliances' }
    ];
    grid.innerHTML = categories.map(cat => `
        <div class="category-card ${cat.cls}" onclick="window.location.href='products.html?category=${cat.name}'">
            <i class="fas ${cat.icon}"></i>
            <p>${cat.name}</p>
        </div>
    `).join('');
}

// ============================================
// HOMEPAGE: FEATURED PRODUCTS
// ============================================
async function loadFeatured() {
    const grid = document.getElementById('featuredGrid');
    if (!grid) return;
    const products = await fetchProducts();
    const featured = products.filter(p => p.featured === true).slice(0, 3);
    if (featured.length === 0) {
        grid.innerHTML = '<p class="loading">No featured products</p>';
        return;
    }
    grid.innerHTML = featured.map(p => productCard(p)).join('');
}

// ============================================
// PRODUCT CARD HTML
// ============================================
function productCard(product) {
    return `
        <div class="product-card">
            <img src="${product.image || 'https://via.placeholder.com/400x400?text=No+Image'}" 
                 alt="${product.name}" class="product-image"
                 onerror="this.src='https://via.placeholder.com/400x400?text=No+Image'" />
            <div class="product-body">
                <div class="product-category">${product.category || 'General'}</div>
                <div class="product-name">${product.name}</div>
                <div class="product-price">${product.price}</div>
                <div class="product-actions">
                    <button class="btn-whatsapp" onclick="orderWhatsApp('${product.id}')">
                        <i class="fab fa-whatsapp"></i> Order via WhatsApp
                    </button>
                    <button class="btn-cart" onclick="addToCartById('${product.id}')">
                        <i class="fas fa-plus"></i> Add to Cart
                    </button>
                </div>
            </div>
        </div>
    `;
}

// ============================================
// WHATSAPP ORDER - REDIRECT TO CHECKOUT
// ============================================
function orderWhatsApp(productId) {
    window.location.href = `checkout.html?product=${productId}`;
}

function addToCartById(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) return;
    addToCart(product);
}

// ============================================
// PRODUCTS PAGE
// ============================================
async function loadProductsPage() {
    const grid = document.getElementById('productsGrid');
    const loading = document.getElementById('loadingProducts');
    const noProducts = document.getElementById('noProducts');
    const categoryFilters = document.getElementById('categoryFilters');

    const urlParams = new URLSearchParams(window.location.search);
    const categoryParam = urlParams.get('category') || '';

    const products = await fetchProducts();
    loading.style.display = 'none';

    const categories = [...new Set(products.map(p => p.category).filter(Boolean))];
    if (categories.length > 0) {
        categoryFilters.innerHTML = `
            <button class="${!categoryParam ? 'active' : ''}" onclick="filterByCategory('')">All</button>
            ${categories.map(c => `
                <button class="${c === categoryParam ? 'active' : ''}" onclick="filterByCategory('${c}')">${c}</button>
            `).join('')}
        `;
    }

    window._currentCategory = categoryParam;
    window._currentSearch = '';

    renderFilteredProducts();

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            window._currentSearch = this.value;
            renderFilteredProducts();
        });
    }
}

function filterByCategory(category) {
    window._currentCategory = category;
    document.querySelectorAll('.category-filters button').forEach(btn => {
        btn.classList.toggle('active', btn.textContent === category || (category === '' && btn.textContent === 'All'));
    });
    renderFilteredProducts();
}

function filterProducts() {
    renderFilteredProducts();
}

function renderFilteredProducts() {
    const grid = document.getElementById('productsGrid');
    const noProducts = document.getElementById('noProducts');
    if (!grid) return;

    const search = window._currentSearch || '';
    const category = window._currentCategory || '';

    let filtered = allProducts;
    if (category) {
        filtered = filtered.filter(p => p.category === category);
    }
    if (search.trim()) {
        const q = search.trim().toLowerCase();
        filtered = filtered.filter(p => 
            p.name.toLowerCase().includes(q) || 
            (p.category && p.category.toLowerCase().includes(q))
        );
    }

    if (filtered.length === 0) {
        grid.innerHTML = '';
        if (noProducts) noProducts.style.display = 'block';
    } else {
        if (noProducts) noProducts.style.display = 'none';
        grid.innerHTML = filtered.map(p => productCard(p)).join('');
    }
}

// ============================================
// CART PAGE
// ============================================
function renderCart() {
    const container = document.getElementById('cartContainer');
    if (!container) return;

    const cart = getCart();

    if (cart.length === 0) {
        container.innerHTML = `
            <div class="cart-empty">
                <i class="fas fa-shopping-cart"></i>
                <p>Your cart is empty</p>
                <a href="products.html" class="btn-primary" style="margin-top:16px;">
                    <i class="fas fa-arrow-left"></i> Browse Products
                </a>
            </div>
        `;
        return;
    }

    let html = '';
    let total = 0;

    cart.forEach((item) => {
        const price = parseFloat(item.price.replace(/[^0-9.]/g, '') || '0');
        const itemTotal = price * (item.quantity || 1);
        total += itemTotal;

        html += `
            <div class="cart-item" data-id="${item.id}">
                <div class="cart-item-info">
                    <img src="${item.image || 'https://via.placeholder.com/64x64?text=No+Image'}" 
                         alt="${item.name}"
                         onerror="this.src='https://via.placeholder.com/64x64?text=No+Image'" />
                    <div class="cart-item-details">
                        <h3>${item.name}</h3>
                        <p>${item.price}</p>
                        <small>${item.category || ''}</small>
                    </div>
                </div>
                <div class="cart-item-controls">
                    <button class="qty-btn" onclick="updateQuantity('${item.id}', -1)">
                        <i class="fas fa-minus"></i>
                    </button>
                    <span class="qty-number">${item.quantity || 1}</span>
                    <button class="qty-btn" onclick="updateQuantity('${item.id}', 1)">
                        <i class="fas fa-plus"></i>
                    </button>
                    <button class="cart-item-remove" onclick="deleteItem('${item.id}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `;
    });

    html += `
        <div class="cart-summary">
            <div class="cart-total">Total: ₦${total.toFixed(2)}</div>
            <div class="cart-actions">
                <a href="checkout.html" class="btn-primary" style="padding:14px 32px; font-size:16px; display:inline-block; text-align:center;">
                    <i class="fas fa-arrow-right"></i> Proceed to Checkout
                </a>
                <button class="btn-danger" onclick="clearCart()">
                    <i class="fas fa-trash"></i> Clear Cart
                </button>
            </div>
        </div>
        <div style="text-align:center; margin-top: 16px;">
            <a href="products.html" style="color:#b8860b; font-weight:500;">
                <i class="fas fa-arrow-left"></i> Continue Shopping
            </a>
        </div>
    `;

    container.innerHTML = html;
}

// ============================================
// UPDATE QUANTITY
// ============================================
function updateQuantity(productId, delta) {
    let cart = getCart();
    const item = cart.find(p => p.id === productId);
    if (!item) return;

    const newQty = (item.quantity || 1) + delta;
    if (newQty <= 0) {
        cart = cart.filter(p => p.id !== productId);
    } else {
        item.quantity = newQty;
    }
    saveCart(cart);
    renderCart();
}

// ============================================
// PROMO OVERLAY (with "Don't show again")
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('promoOverlay');
    if (overlay) {
        const closeBtn = document.getElementById('promoClose');
        const skipLink = document.getElementById('promoSkipLink');
        const dontShowCheckbox = document.getElementById('dontShowAgain');

        // Check localStorage for permanent hide preference
        if (localStorage.getItem('promoHidden') === 'true') {
            overlay.classList.add('hidden');
        } else {
            overlay.classList.remove('hidden');
        }

        function dismissPromo() {
            overlay.classList.add('hidden');
            if (dontShowCheckbox && dontShowCheckbox.checked) {
                localStorage.setItem('promoHidden', 'true');
            }
        }

        if (closeBtn) closeBtn.addEventListener('click', dismissPromo);
        if (skipLink) {
            skipLink.addEventListener('click', function(e) {
                e.preventDefault();
                dismissPromo();
            });
        }
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                dismissPromo();
            }
        });
    }

    // Update cart badge on every page load
    updateCartBadge();
});

// ============================================
// EXPOSE FUNCTIONS TO GLOBAL SCOPE
// ============================================
window.orderWhatsApp = orderWhatsApp;
window.addToCartById = addToCartById;
window.removeFromCart = removeFromCart;
window.deleteItem = deleteItem;
window.clearCart = clearCart;
window.updateQuantity = updateQuantity;
window.filterByCategory = filterByCategory;
window.filterProducts = filterProducts;
window.toggleMobileMenu = toggleMobileMenu;

// ============================================
// INIT (runs after DOM is ready)
// ============================================
document.addEventListener('DOMContentLoaded', async function() {
    // First check maintenance mode
    const maintenanceOn = await checkMaintenance();
    if (maintenanceOn) {
        // Maintenance page already shown, stop further execution
        return;
    }

    // If not in maintenance, continue normal initialization
    updateCartBadge();
});