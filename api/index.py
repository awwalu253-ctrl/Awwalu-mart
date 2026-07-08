import os
import json
from fastapi import FastAPI
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

def get_products() -> List[Dict]:
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
        print(f"ERROR: {e}")
        return []

# ----- ROUTES -----

@app.get("/")
async def root():
    return {"message": "Hello from Vercel!"}

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