import os
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
        
        cred_path = os.path.join(os.path.dirname(__file__), "credentials.json")
        creds = Credentials.from_service_account_file(cred_path, scopes=scope)
        client = gspread.authorize(creds)
        
        SHEET_ID = "1ZcHPR7V30AXlKAeaVAzaVn-F3Hk2hNSh8LicIBfloyo"
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        rows = sheet.get_all_records()
        
        products = []
        for row in rows:
            # Debug: print each row to terminal
            print(f"DEBUG: Row = {row}")
            
            # Check if Stock column exists and is "Yes"
            stock_value = str(row.get("Stock", "")).lower()
            print(f"DEBUG: Stock value = '{stock_value}'")
            
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

@app.get("/api/products")
async def get_all_products():
    return get_products()

@app.get("/api/products/featured")
async def get_featured_products():
    all_products = get_products()
    return [p for p in all_products if p.get("featured", False)]

@app.get("/api/test")
async def test_connection():
    return {"status": "ok", "message": "API is running"}

@app.get("/api/debug-credentials")
async def debug_credentials():
    cred_path = os.path.join(os.path.dirname(__file__), "credentials.json")
    return {
        "file_exists": os.path.exists(cred_path),
        "path": cred_path,
        "current_directory": os.getcwd(),
        "files_in_api_folder": os.listdir(os.path.dirname(__file__)) if os.path.exists(os.path.dirname(__file__)) else []
    }

@app.get("/api/debug-sheet")
async def debug_sheet():
    """Shows raw sheet data to debug the issue"""
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        cred_path = os.path.join(os.path.dirname(__file__), "credentials.json")
        creds = Credentials.from_service_account_file(cred_path, scopes=scope)
        client = gspread.authorize(creds)
        
        SHEET_ID = "1ZcHPR7V30AXlKAeaVAzaVn-F3Hk2hNSh8LicIBfloyo"
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        
        # Get all values as a list of lists (raw data)
        all_values = sheet.get_all_values()
        
        # Get all records (dictionary format)
        all_records = sheet.get_all_records()
        
        return {
            "row_count": len(all_values),
            "headers": all_values[0] if all_values else [],
            "first_3_rows": all_values[:3] if all_values else [],
            "all_records_count": len(all_records),
            "first_record": all_records[0] if all_records else None,
            "all_records": all_records
        }
    except Exception as e:
        return {"error": str(e)}