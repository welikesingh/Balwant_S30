# uvicorn neon_dbOrderAPI:app --reload --port 8000

import os
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import FastAPI , Depends, HTTPException

load_dotenv()

DATABASE_URL = os.getenv("NEON_DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def check_database_connection():
    try:
        # Attempt to connect to the database
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
    return True

check_database_connection()

app = FastAPI(title="neon db test" , 
              description="API to test connection with Neon PostgreSQL database",
              version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

# ------------------------------------------
# ---------------- Customers ----------------

@app.get("/customers")
def get_customers():
    try:
        with SessionLocal() as session:
            result = session.execute(
                text("SELECT * FROM customers ORDER BY customer_id")
            ).mappings().fetchall()
            return [dict(row) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching customers: {e}")


@app.get("/customer/{customer_id}")
def get_customer(customer_id: int):
    try:
        with SessionLocal() as session:
            result = session.execute(
                text("SELECT * FROM customers where customer_id = :customer_id"),
                {"customer_id": customer_id}
            ).fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Customer not found")
            return {"customer_id": result[0], "name": result[1], "email": result[2], "phone": result[3],"address": result[4],"created_at": result[5]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching customers: {e}")


# ------------------------------------------
# ---------------- Products ----------------

@app.get("/products")
def get_products():
    try:
        with SessionLocal() as session:
            result = session.execute(
                text("SELECT * FROM products ORDER BY product_id")
            ).mappings().fetchall()
            return [dict(row) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {e}")


@app.get("/products/{product_id}")
def get_product(product_id: int):
    try:
        with SessionLocal() as session:
            result = session.execute(
                text("SELECT * FROM products WHERE product_id = :product_id"),
                {"product_id": product_id}
            ).fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Product not found")
            return {"product_id": result[0], "product_name": result[1], "description": result[2], "price": result[3], "stock_quantity": result[4], "is_active": result[5]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {e}")


class ProductCreate(BaseModel):
    product_name: str = Field(
        min_length=1,
        max_length=150
    )
    description: Optional[str] = None
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    stock_quantity: Decimal  = Field(default=0, ge=0)
    is_active: bool = True
    
    
@app.post("/product")
def create_product(product: ProductCreate):
    try:
        with SessionLocal() as session:
            session.execute(
                text("INSERT INTO products (product_name, description, price, stock_quantity, is_active) VALUES (:product_name, :description, :price, :stock_quantity, :is_active)"),
                {"product_name": product.product_name, "description": product.description, "price": product.price, "stock_quantity": product.stock_quantity, "is_active": product.is_active}
            )
            session.commit()
        return {"message": "Product created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating product: {e}")


# ---------------- Orders ----------------
from typing import Literal
OrderStatus = Literal["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]

class OrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    total_amount: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=2)
    status: OrderStatus = "PENDING"
    order_quantity: int = Field(gt=0)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

def validate_customer_exists(session, customer_id: int):
    result = session.execute(
        text("SELECT 1 FROM customers WHERE customer_id = :customer_id"),
        {"customer_id": customer_id}
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    return True

def validate_product_exists(session, product_id: int):
    result = session.execute(
        text("SELECT 1 FROM products WHERE product_id = :product_id"),
        {"product_id": product_id}
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return True

def validate_stock(session, product_id: int, quantity: int):
    result = session.execute(
        text("SELECT stock_quantity FROM products WHERE product_id = :product_id"),
        {"product_id": product_id}
    ).fetchone()
    if result[0] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    return True

def calculate_total_amount(session, product_id: int, quantity: int):
    result = session.execute(
        text("SELECT price FROM products WHERE product_id = :product_id"),
        {"product_id": product_id}
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result[0] * quantity

@app.post("/orders", status_code=201)
def create_order(order: OrderCreate):
    try:
        with SessionLocal() as session:
            # Wrap the multi-line condition in parentheses
            if (
                validate_customer_exists(session, order.customer_id)
                and validate_product_exists(session, order.product_id)
                and validate_stock(session, order.product_id, order.order_quantity)
            ): 
                order.total_amount = calculate_total_amount(session, order.product_id, order.order_quantity)
                result = session.execute(
                    text(
                        "INSERT INTO orders (customer_id, status, total_amount, product_id, order_quantity ) "
                        "VALUES (:customer_id, :status, :total_amount, :product_id, :order_quantity) RETURNING *"
                    ),
                    {
                        "customer_id": order.customer_id,
                        "status": order.status,
                        "total_amount": order.total_amount,
                        "product_id": order.product_id,
                        "order_quantity": order.order_quantity,
                    },
                ).mappings().fetchone()
                session.commit()
                return dict(result)
            # Handle failed validation explicitly
            raise HTTPException(status_code=400, detail="Invalid customer, product, or insufficient stock")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {e}")
    

@app.get("/orders")
def get_orders():
    try:
        with SessionLocal() as session:
            result = session.execute(
                text("SELECT * FROM orders ORDER BY order_id")
            ).mappings().fetchall()
            return [dict(row) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {e}")


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    try:
        with SessionLocal() as session:
            result = session.execute(
                text("SELECT * FROM orders WHERE order_id = :order_id"),
                {"order_id": order_id}
            ).mappings().fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Order not found")
            return dict(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching order: {e}")


@app.put("/orders/{order_id}/status")
def update_order_status(order_id: int, payload: OrderStatusUpdate):
    try:
        with SessionLocal() as session:
            result = session.execute(
                text("UPDATE orders SET status = :status WHERE order_id = :order_id RETURNING *"),
                {"status": payload.status, "order_id": order_id}
            ).mappings().fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Order not found")
            session.commit()
            return dict(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating order status: {e}")
