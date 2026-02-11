import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel, Field, validator

# --- SETUP ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secureorder-pro")

mcp = FastMCP("SecureOrder-Pro")
DB_PATH = os.getenv("SQLITE_DB_PATH", "secure_orders.db")

# --- 🧠 PYDANTIC MODELS (The Security Layer) ---
class OrderRequest(BaseModel):
    customer_id: int = Field(..., description="Unique ID of the customer")
    product_id: int = Field(..., description="ID of the product to buy")
    quantity: int = Field(..., gt=0, lt=50, description="Quantity (Max 50 per order for security)")

class CancelRequest(BaseModel):
    order_id: int = Field(..., description="The ID of the order to cancel")
    reason: str = Field(..., min_length=10, description="Minimum 10 character reason for cancellation")

# --- 🏗️ DATABASE INITIALIZATION (Relational & Complex) ---
def init_robust_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Products Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            price REAL,
            stock INTEGER,
            category TEXT
        )
    """)
    
    # 2. Orders Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_id INTEGER,
            status TEXT, -- 'pending', 'shipped', 'cancelled'
            order_date TIMESTAMP,
            delivery_date TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    # Seed Imaginary Industrial Data
    products = [
        (1, 'Quantum CPU', 1200.00, 45, 'Hardware'),
        (2, 'Neural Link v2', 850.50, 10, 'Neural-Interfaces'),
        (3, 'Security Token', 45.00, 200, 'Security')
    ]
    cursor.executemany("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)", products)
    
    # Seed an imaginary 'shipped' order to test policy protection
    cursor.execute("""
        INSERT OR IGNORE INTO orders (id, customer_id, product_id, status, order_date, delivery_date) 
        VALUES (101, 500, 1, 'shipped', '2026-02-01', '2026-02-05')
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ Robust Database and Policy Tables Ready.")

# --- 🛠️ INDUSTRIAL TOOLS ---

@mcp.tool()
async def search_products(query: str) -> str:
    """Search the product catalog using fuzzy matching to prevent agent hallucination."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, stock FROM products WHERE name LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        return f"No products found matching '{query}'."
    
    output = "📦 Available Products:\n"
    for r in results:
        output += f"- {r[0]}: ${r[1]} (Stock: {r[2]})\n"
    return output

@mcp.tool()
async def place_order(request: OrderRequest) -> str:
    """Places a new order with atomic stock validation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check stock
        cursor.execute("SELECT stock, name FROM products WHERE id = ?", (request.product_id,))
        prod = cursor.fetchone()
        
        if not prod or prod[0] < request.quantity:
            return "❌ Order Failed: Insufficient stock or invalid product ID."
        
        # Deduct stock & Create Order (Atomic Transaction)
        cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (request.quantity, request.product_id))
        
        delivery_days = int(os.getenv("DELIVERY_DAYS_OFFSET", 3))
        delivery_date = datetime.now() + timedelta(days=delivery_days)
        
        cursor.execute("""
            INSERT INTO orders (customer_id, product_id, status, order_date, delivery_date)
            VALUES (?, ?, 'pending', ?, ?)
        """, (request.customer_id, request.product_id, datetime.now(), delivery_date))
        
        order_id = cursor.lastrowid
        conn.commit()
        return f"✅ Success! Order #{order_id} placed. Estimated delivery: {delivery_date.strftime('%Y-%m-%d')}."
    except Exception as e:
        conn.rollback()
        return f"❌ System Error: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
async def cancel_order(request: CancelRequest) -> str:
    """Cancels an order ONLY if it hasn't shipped yet (Company Policy Enforcement)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT status FROM orders WHERE id = ?", (request.order_id,))
    row = cursor.fetchone()
    
    if not row:
        return f"❌ Error: Order #{request.order_id} not found."
    
    status = row[0]
    if status in ['shipped', 'delivered']:
        return f"🚫 Policy Restriction: Order #{request.order_id} is '{status}' and cannot be cancelled."
    
    cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (request.order_id,))
    conn.commit()
    conn.close()
    return f"✅ Order #{request.order_id} cancelled. Reason: {request.reason}"

if __name__ == "__main__":
    init_robust_db()
    mcp.run(transport="sse", host=os.getenv("HOST"), port=int(os.getenv("PORT")))