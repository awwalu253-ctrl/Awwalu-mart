import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict

# ---------- FastAPI App ----------
app = FastAPI()

# Enable CORS for all origins (needed for your frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Helper: Fetch Products from Google Sheets ----------
def get_products() -> List[Dict]:
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # On Vercel, use environment variable; locally, use credentials.json
        if os.getenv("GOOGLE_CREDENTIALS"):
            creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        else:
            # Local development – credentials.json must be in the same folder
            cred_path = os.path.join(os.path.dirname(__file__), "credentials.json")
            creds = Credentials.from_service_account_file(cred_path, scopes=scope)

        client = gspread.authorize(creds)

        # Replace with your actual Sheet ID
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

# ---------- API Routes ----------

@app.get("/")
async def root():
    """Welcome message for the API root."""
    return {
        "message": "Welcome to Awwalu Kitchen Vault API",
        "endpoints": ["/api/products", "/api/products/featured", "/api/products/{id}", "/api/test", "/api/debug"]
    }

@app.get("/api/test")
async def test_connection():
    """Simple test endpoint to verify the API is running."""
    return {"status": "ok", "message": "API is running"}

@app.get("/api/products")
async def get_all_products():
    """Returns all products from Google Sheets (stock = Yes)."""
    return get_products()

@app.get("/api/products/featured")
async def get_featured_products():
    """Returns only featured products."""
    all_products = get_products()
    return [p for p in all_products if p.get("featured", False)]

@app.get("/api/products/{product_id}")
async def get_product_by_id(product_id: str):
    """
    Returns a single product by its ID.
    Example: /api/products/prod_001
    """
    all_products = get_products()
    for product in all_products:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/api/debug")
async def debug():
    """
    Debug endpoint to check environment and sheet connectivity.
    Useful for troubleshooting.
    """
    result = {
        "has_credentials_env": bool(os.getenv("GOOGLE_CREDENTIALS")),
        "sheet_id": "1ZcHPR7V30AXlKAeaVAzaVn-F3Hk2hNSh8LicIBfloyo",
        "products_count": 0,
        "error": None
    }
    try:
        products = get_products()
        result["products_count"] = len(products)
    except Exception as e:
        result["error"] = str(e)
    return result

# ============================================
# BUNDLES
# ============================================

def get_bundles() -> List[Dict]:
    """Fetch bundles from Google Sheets."""
    try:
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

        client = gspread.authorize(creds)
        SHEET_ID = "YOUR_GOOGLE_SHEET_ID"

        # Open the "Bundles" sheet
        try:
            sheet = client.open_by_key(SHEET_ID).worksheet("Bundles")
        except gspread.WorksheetNotFound:
            # If sheet doesn't exist, try the first sheet
            sheet = client.open_by_key(SHEET_ID).sheet1

        rows = sheet.get_all_records()

        bundles = []
        for row in rows:
            if row.get("Bundle Name", "").strip():
                # Parse product IDs (comma-separated)
                product_ids = [p.strip() for p in str(row.get("Product IDs", "")).split(",") if p.strip()]
                bundles.append({
                    "id": str(row.get("Bundle ID", "")),
                    "name": str(row.get("Bundle Name", "")),
                    "description": str(row.get("Description", "")),
                    "discount": float(str(row.get("Discount %", "0")).replace("%", "").strip() or 0),
                    "product_ids": product_ids,
                    "image": str(row.get("Image URL", ""))
                })
        return bundles

    except Exception as e:
        print(f"ERROR in get_bundles: {e}")
        return []

@app.get("/api/bundles")
async def get_all_bundles():
    """Returns all bundles."""
    return get_bundles()

@app.get("/api/bundles/{bundle_id}")
async def get_bundle_by_id(bundle_id: str):
    """Returns a single bundle by its ID."""
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

# (Optional) For local development using `uvicorn api.index:app --reload`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)