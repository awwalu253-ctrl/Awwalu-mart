// ============================================
// API BASE URL (auto-detect)
// ============================================
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api'
    : '/api';

// ============================================
// NAVBAR & FOOTER
// ============================================
function loadNavbar() {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;
    navbar.innerHTML = `
        <div class="container">
            <a href="index.html">
                <img src="logo.png" alt="Awwalu Kitchen Vault" class="logo" />
            </a>
            <div class="nav-links">
                <a href="index.html" class="${window.location.pathname.includes('index') ? 'active' : ''}">Home</a>
                <a href="products.html" class="${window.location.pathname.includes('products') ? 'active' : ''}">Products</a>
                <a href="about.html" class="${window.location.pathname.includes('about') ? 'active' : ''}">About</a>
                <a href="contact.html" class="${window.location.pathname.includes('contact') ? 'active' : ''}">Contact</a>
                <span class="cart-icon" onclick="window.location.href='cart.html'">
                    <i class="fas fa-shopping-cart"></i>
                    <span class="cart-badge" id="cartBadgeNav">0</span>
                </span>
            </div>
            <button class="hamburger" onclick="toggleMobileMenu()">
                <i class="fas fa-bars"></i>
            </button>
        </div>
        <div class="mobile-menu" id="mobileMenu">
            <a href="index.html">Home</a>
            <a href="products.html">Products</a>
            <a href="about.html">About</a>
            <a href="contact.html">Contact</a>
            <a href="cart.html">Cart (<span id="mobileCartCount">0</span>)</a>
        </div>
    `;
    updateCartBadge();
}

function loadFooter() {
    const footer = document.getElementById('footer');
    if (!footer) return;
    footer.innerHTML = `
        <div class="container">
            <img src="logo.png" alt="Awwalu Kitchen Vault" style="height:48px; margin-bottom:12px;" />
            <p>&copy; 2026 Awwalu Kitchen Vault. All rights reserved.</p>
            <p class="small">Premium kitchen appliances, cookware, and utensils.</p>
        </div>
    `;
}

function toggleMobileMenu() {
    document.getElementById('mobileMenu').classList.toggle('open');
}

// ============================================
// CART MANAGEMENT
// ============================================
let cart = JSON.parse(localStorage.getItem('awwalumart-cart') || '[]');

function updateCartBadge() {
    const count = cart.length;
    document.querySelectorAll('.cart-badge').forEach(el => {
        el.textContent = count;
        el.classList.toggle('show', count > 0);
    });
    document.getElementById('mobileCartCount') && (document.getElementById('mobileCartCount').textContent = count);
}

function addToCart(product) {
    const existing = cart.find(p => p.id === product.id);
    if (existing) {
        showToast(`${product.name} is already in your cart!`);
        return;
    }
    cart.push(product);
    localStorage.setItem('awwalumart-cart', JSON.stringify(cart));
    updateCartBadge();
    showToast(`✅ ${product.name} added to cart!`);
}

function removeFromCart(productId) {
    cart = cart.filter(p => p.id !== productId);
    localStorage.setItem('awwalumart-cart', JSON.stringify(cart));
    updateCartBadge();
    renderCart();
}

function clearCart() {
    cart = [];
    localStorage.setItem('awwalumart-cart', JSON.stringify(cart));
    updateCartBadge();
    renderCart();
}

function getCartTotal() {
    return cart.reduce((sum, p) => {
        const price = parseFloat(p.price.replace(/[^0-9.]/g, '') || '0');
        return sum + price;
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

function orderWhatsApp(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) return;
    const message = `Hi! I want to order: ${product.name} (${product.price})`;
    const url = `https://wa.me/234XXXXXXXXX?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
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

    document.getElementById('searchInput').addEventListener('input', function() {
        window._currentSearch = this.value;
        renderFilteredProducts();
    });
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
        noProducts.style.display = 'block';
    } else {
        noProducts.style.display = 'none';
        grid.innerHTML = filtered.map(p => productCard(p)).join('');
    }
}

// ============================================
// CART PAGE
// ============================================
function renderCart() {
    const container = document.getElementById('cartContainer');
    if (!container) return;

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
    cart.forEach((item) => {
        html += `
            <div class="cart-item">
                <div class="cart-item-info">
                    <img src="${item.image || 'https://via.placeholder.com/64x64?text=No+Image'}" alt="${item.name}" />
                    <div class="cart-item-details">
                        <h3>${item.name}</h3>
                        <p>${item.price}</p>
                        <small>${item.category || ''}</small>
                    </div>
                </div>
                <button class="cart-item-remove" onclick="removeFromCart('${item.id}')">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>
        `;
    });

    const total = getCartTotal();
    html += `
        <div class="cart-summary">
            <div class="cart-total">Total: ₦${total.toFixed(2)}</div>
            <div class="cart-actions">
                <button class="btn-whatsapp" onclick="orderCartWhatsApp()">
                    <i class="fab fa-whatsapp"></i> Order All via WhatsApp
                </button>
                <button class="btn-danger" onclick="clearCart()">
                    <i class="fas fa-trash"></i> Clear Cart
                </button>
            </div>
        </div>
        <div style="text-align:center; margin-top: 16px;">
            <a href="products.html" style="color:#16a34a; font-weight:500;">
                <i class="fas fa-arrow-left"></i> Continue Shopping
            </a>
        </div>
    `;

    container.innerHTML = html;
}

function orderCartWhatsApp() {
    if (cart.length === 0) return;
    const items = cart.map(p => `- ${p.name} (${p.price})`).join('\n');
    const total = getCartTotal();
    const message = `🛒 *Awwalu Kitchen Vault Order*\n\n${items}\n\n*Total: ₦${total.toFixed(2)}*\n\nThank you for shopping with Awwalu Kitchen Vault! 🎉`;
    const url = `https://wa.me/234XXXXXXXXX?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
}

// ============================================
// INIT
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    updateCartBadge();
});