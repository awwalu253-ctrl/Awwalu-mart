import os
import json
import uuid
import jwt
from datetime import datetime, timedelta
from typing import List, Dict
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import gspread
from google.oauth2.service_account import Credentials

# ---------- FastAPI App ----------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Admin & JWT Configuration ----------
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
JWT_SECRET = ADMIN_PASSWORD
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

# ---------- Google Sheets Helpers ----------
SHEET_ID = "1ZcHPR7V30AXlKAeaVAzaVn-F3Hk2hNSh8LicIBfloyo"

def get_gspread_client():
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

def get_sheet(sheet_name):
    client = get_gspread_client()
    try:
        return client.open_by_key(SHEET_ID).worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        return client.open_by_key(SHEET_ID).add_worksheet(title=sheet_name, rows=100, cols=10)

def get_config():
    try:
        sheet = get_sheet("Config")
        records = sheet.get_all_records()
        config = {}
        for row in records:
            if "Setting" in row and "Value" in row:
                config[row["Setting"]] = row["Value"]
        return config
    except Exception:
        return {"maintenance_mode": "No"}

def update_config(setting, value):
    try:
        sheet = get_sheet("Config")
        records = sheet.get_all_records()
        # Ensure headers exist
        if not records or "Setting" not in records[0] or "Value" not in records[0]:
            sheet.update_cell(1, 1, "Setting")
            sheet.update_cell(1, 2, "Value")
        for i, row in enumerate(records, start=2):
            if row.get("Setting") == setting:
                sheet.update_cell(i, 2, value)
                return
        sheet.append_row([setting, value])
    except Exception as e:
        print(f"Error updating Config: {e}")

# ---------- JWT Functions ----------
def create_token(username: str) -> str:
    payload = {
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("username") == "admin"
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

# ---------- Products ----------
def get_products() -> List[Dict]:
    try:
        client = get_gspread_client()
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
                    "featured": str(row.get("Featured", "")).lower() in ["yes", "true"],
                    "stock": str(row.get("Stock", "Yes"))
                })
        return products
    except Exception as e:
        print(f"ERROR in get_products: {e}")
        return []

# ---------- Bundles ----------
def get_bundles() -> List[Dict]:
    try:
        sheet = get_sheet("Bundles")
        rows = sheet.get_all_records()
        bundles = []
        for row in rows:
            if not row.get("Bundle Name", "").strip():
                continue
            product_ids_str = str(row.get("Product IDs", "")).strip()
            product_ids = [p.strip() for p in product_ids_str.split(",") if p.strip()]
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

# ---------- Admin Authentication ----------
@app.post("/api/admin/login")
async def admin_login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if username == "admin" and password == ADMIN_PASSWORD:
        token = create_token(username)
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/admin/logout")
async def admin_logout():
    return {"message": "Logged out"}

def admin_required(auth: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    if not verify_token(auth.credentials):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

# ---------- Coupon Endpoints ----------
@app.get("/api/admin/coupons")
async def get_coupons(_=Depends(admin_required)):
    sheet = get_sheet("Coupons")
    return sheet.get_all_records()

@app.post("/api/admin/coupons")
async def create_coupon(data: dict, _=Depends(admin_required)):
    sheet = get_sheet("Coupons")
    required = ["code", "discount_type", "discount_value", "expiry_date", "usage_limit"]
    for field in required:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")
    sheet.append_row([
        data["code"],
        data["discount_type"],
        data["discount_value"],
        data["expiry_date"],
        data["usage_limit"],
        0,  # used count
        data.get("active", "Yes"),
        data.get("min_order", 0)  # Min Order Amount
    ])
    return {"message": "Coupon created"}

@app.put("/api/admin/coupons/{code}")
async def update_coupon(code: str, data: dict, _=Depends(admin_required)):
    sheet = get_sheet("Coupons")
    records = sheet.get_all_records()
    col_map = {
        "discount_type": 2,
        "discount_value": 3,
        "expiry_date": 4,
        "usage_limit": 5,
        "active": 7,
        "min_order": 8  # Min Order Amount column
    }
    for i, row in enumerate(records, start=2):
        if row["Code"] == code:
            for key, value in data.items():
                if key in col_map:
                    sheet.update_cell(i, col_map[key], value)
            return {"message": "Coupon updated"}
    raise HTTPException(status_code=404, detail="Coupon not found")

@app.delete("/api/admin/coupons/{code}")
async def delete_coupon(code: str, _=Depends(admin_required)):
    sheet = get_sheet("Coupons")
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Code"] == code:
            sheet.delete_rows(i)
            return {"message": "Coupon deleted"}
    raise HTTPException(status_code=404, detail="Coupon not found")

# ---------- Public Coupon Validation ----------
@app.get("/api/validate-coupon")
async def validate_coupon(code: str, total: float = 0):
    """
    Validate a coupon code with an optional order total.
    Query params: ?code=SAVE10&total=5000
    """
    try:
        sheet = get_sheet("Coupons")
        records = sheet.get_all_records()
        for row in records:
            if row.get("Code") == code:
                # Check active
                if row.get("Active") != "Yes":
                    return {"valid": False, "reason": "Coupon is not active"}
                # Check expiry
                expiry = row.get("Expiry Date")
                if expiry:
                    try:
                        expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                        if expiry_date < datetime.now():
                            return {"valid": False, "reason": "Coupon has expired"}
                    except:
                        pass
                # Check usage limit
                used = int(row.get("Used Count") or 0)
                limit = int(row.get("Usage Limit") or 0)
                if limit > 0 and used >= limit:
                    return {"valid": False, "reason": "Coupon usage limit reached"}

                # --- NEW: Check minimum order amount ---
                min_order = float(row.get("Min Order Amount") or 0)
                if min_order > 0 and total < min_order:
                    return {
                        "valid": False,
                        "reason": f"Minimum order of ₦{min_order:,.2f} required"
                    }

                # Return discount info
                return {
                    "valid": True,
                    "discount_type": row.get("Discount Type"),  # percentage or fixed
                    "discount_value": float(row.get("Discount Value") or 0),
                    "code": code,
                    "min_order": min_order
                }
        return {"valid": False, "reason": "Coupon not found"}
    except Exception as e:
        print(f"Error validating coupon: {e}")
        return {"valid": False, "reason": "Server error"}

# ---------- Maintenance Mode ----------
@app.get("/api/admin/maintenance")
async def get_maintenance(_=Depends(admin_required)):
    config = get_config()
    return {"maintenance_mode": config.get("maintenance_mode", "No")}

@app.post("/api/admin/maintenance")
async def toggle_maintenance(data: dict, _=Depends(admin_required)):
    mode = data.get("mode", "No")
    if mode not in ["Yes", "No"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    update_config("maintenance_mode", mode)
    return {"maintenance_mode": mode}

@app.get("/api/maintenance")
async def check_maintenance():
    config = get_config()
    return {"maintenance": config.get("maintenance_mode", "No") == "Yes"}

# ---------- Orders ----------
@app.get("/api/admin/orders")
async def get_orders(_=Depends(admin_required)):
    try:
        sheet = get_sheet("Orders")
        return sheet.get_all_records()
    except:
        return []

@app.post("/api/admin/orders")
async def log_order(data: dict, _=Depends(admin_required)):
    try:
        sheet = get_sheet("Orders")
        sheet.append_row([
            str(uuid.uuid4())[:8],
            str(datetime.utcnow()),
            data.get("customer_name", ""),
            data.get("phone", ""),
            data.get("address", ""),
            data.get("items", ""),
            data.get("total", "0"),
            "Pending"
        ])
        return {"message": "Order logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Admin Product Management ----------
@app.post("/api/admin/products")
async def create_product(data: dict, _=Depends(admin_required)):
    try:
        sheet = get_gspread_client().open_by_key(SHEET_ID).sheet1
        sheet.append_row([
            data.get("id", ""),
            data.get("name", ""),
            data.get("price", ""),
            data.get("image", ""),
            data.get("category", ""),
            data.get("description", ""),
            data.get("stock", "Yes"),
            data.get("featured", "No")
        ])
        return {"message": "Product created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/products/{product_id}")
async def update_product(product_id: str, data: dict, _=Depends(admin_required)):
    try:
        sheet = get_gspread_client().open_by_key(SHEET_ID).sheet1
        records = sheet.get_all_records()
        col_map = {"name": 2, "price": 3, "image": 4, "category": 5, "description": 6, "stock": 7, "featured": 8}
        for i, row in enumerate(records, start=2):
            if row.get("Product ID") == product_id:
                for key, value in data.items():
                    if key in col_map:
                        sheet.update_cell(i, col_map[key], value)
                return {"message": "Product updated"}
        raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/products/{product_id}")
async def delete_product(product_id: str, _=Depends(admin_required)):
    try:
        sheet = get_gspread_client().open_by_key(SHEET_ID).sheet1
        records = sheet.get_all_records()
        for i, row in enumerate(records, start=2):
            if row.get("Product ID") == product_id:
                sheet.delete_rows(i)
                return {"message": "Product deleted"}
        raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Public API Routes ----------
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
            "/api/debug",
            "/api/maintenance",
            "/api/admin/login",
            "/api/validate-coupon"
        ]
    }

@app.get("/api/test")
async def test():
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
    return get_bundles()

@app.get("/api/bundles/{bundle_id}")
async def get_bundle_by_id(bundle_id: str):
    all_bundles = get_bundles()
    for bundle in all_bundles:
        if bundle["id"] == bundle_id:
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
    try:
        products = get_products()
        bundles = get_bundles()
        config = get_config()
        return {
            "has_credentials_env": bool(os.getenv("GOOGLE_CREDENTIALS")),
            "sheet_id": SHEET_ID,
            "products_count": len(products),
            "bundles_count": len(bundles),
            "maintenance_mode": config.get("maintenance_mode", "No")
        }
    except Exception as e:
        return {"error": str(e)}

# ---------- Local Development ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)