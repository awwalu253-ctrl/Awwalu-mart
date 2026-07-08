import os
import json
from fastapi import FastAPI
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

# ---------- Helper: Fetch products from Google Sheets ----------
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
    return {"message": "Welcome to Awwalumart API", "endpoints": ["/api/products", "/api/test", "/api/debug"]}

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

@app.get("/api/debug")
async def debug():
    """Debug endpoint to check environment and sheet connectivity."""
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