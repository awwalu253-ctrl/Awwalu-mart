import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# HELPERS
# ============================================

def get_gspread_client():
    """Get authenticated gspread client."""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    if os.getenv("GOOGLE_CREDENTIALS"):
        creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    else:
        cred_path = os.path.join(os.path.dirname(__file__), "credentials.json")
        creds = Credentials.from_service_account_file(cred_path, scopes=scope)

    return gspread.authorize(creds)

def get_products() -> List[Dict]:
    """Fetch products from Google Sheets."""
    try:
        client = get_gspread_client()
        SHEET_ID = "1ZcHPR7V30AXlKAeaVAzaVn-F3Hk2hNSh8LicIBfloyo"

        sheet = client.open_by_key(SHEET_ID).sheet1
        rows = sheet.get_all_records()

        products = []
        for row in rows:
            stock_value = str(row.get("Stock", "")).lower()
            if stock_value == "yes" or stock_value == "true":
                products.append({
                    "id": str(row.get("Product ID", "")),
                    "name": str(row.get("Product Name", "")),
                    "price": str(row.get("Price", "")),
                    "image": str(row.get("Image URL", "")),
                    "category": str(row.get("Category", "")),
                    "description": str(row.get("Description", "")),
                    "featured": str(row.get("Featured", "")).lower() in ["yes", "true"]
                })
        return products

    except Exception as e:
        print(f"ERROR in get_products: {e}")
        return []

def get_bundles() -> List[Dict]:
    """Fetch bundles from Google Sheets."""
    try:
        client = get_gspread_client()
        SHEET_ID = "1ZcHPR7V30AXlKAeaVAzaVn-F3Hk2hNSh8LicIBfloyo"

        # Try to open the "Bundles" sheet
        try:
            sheet = client.open_by_key(SHEET_ID).worksheet("Bundles")
        except gspread.WorksheetNotFound:
            print("Sheet 'Bundles' not found. Looking for first sheet...")
            sheet = client.open_by_key(SHEET_ID).sheet1

        rows = sheet.get_all_records()
        print(f"Found {len(rows)} rows in Bundles sheet")

        bundles = []
        for row in rows:
            # Skip empty rows
            if not row.get("Bundle Name", "").strip():
                continue

            # Parse product IDs (comma-separated)
            product_ids_str = str(row.get("Product IDs", "")).strip()
            product_ids = [p.strip() for p in product_ids_str.split(",") if p.strip()]

            bundle = {
                "id": str(row.get("Bundle ID", "")),
                "name": str(row.get("Bundle Name", "")),
                "description": str(row.get("Description", "")),
                "discount": float(str(row.get("Discount %", "0")).replace("%", "").strip() or 0),
                "product_ids": product_ids,
                "image": str(row.get("Image URL", ""))
            }
            bundles.append(bundle)

        return bundles

    except Exception as e:
        print(f"ERROR in get_bundles: {e}")
        return []

# ============================================
# API ROUTES
# ============================================

@app.get("/")
async def root():
    return {
        "message": "Welcome to Awwalu Kitchen Vault API",
        "endpoints": [
            "/api/products",
            "/api/products/featured",
            "/api/products/{id}",
            "/api/bundles",
            "/api/bundles/{id}",
            "/api/test",
            "/api/debug"
        ]
    }

@app.get("/api/test")
async def test_connection():
    return {"status": "ok", "message": "API is running"}

@app.get("/api/products")
async def get_all_products():
    return get_products()

@app.get("/api/products/featured")
async def get_featured_products():
    all_products = get_products()
    return [p for p in all_products if p.get("featured", False)]

@app.get("/api/products/{product_id}")
async def get_product_by_id(product_id: str):
    all_products = get_products()
    for product in all_products:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/api/bundles")
async def get_all_bundles():
    """Returns all bundles."""
    return get_bundles()

@app.get("/api/bundles/{bundle_id}")
async def get_bundle_by_id(bundle_id: str):
    """Returns a single bundle with full product details."""
    all_bundles = get_bundles()
    for bundle in all_bundles:
        if bundle["id"] == bundle_id:
            # Get full product details for each product ID
            all_products = get_products()
            products = []
            for pid in bundle["product_ids"]:
                for product in all_products:
                    if product["id"] == pid:
                        products.append(product)
                        break
            bundle["products"] = products
            return bundle
    raise HTTPException(status_code=404, detail="Bundle not found")

@app.get("/api/debug")
async def debug():
    result = {
        "has_credentials_env": bool(os.getenv("GOOGLE_CREDENTIALS")),
        "sheet_id": "1ZcHPR7V30AXlKAeaVAzaVn-F3Hk2hNSh8LicIBfloyo",
        "products_count": 0,
        "bundles_count": 0,
        "error": None
    }
    try:
        products = get_products()
        result["products_count"] = len(products)
    except Exception as e:
        result["error"] = str(e)
    try:
        bundles = get_bundles()
        result["bundles_count"] = len(bundles)
    except Exception as e:
        result["error"] = str(e)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)