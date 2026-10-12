# Order E-Commerce API (Neon PostgreSQL)

FastAPI service connected to a Neon PostgreSQL database for customers, products, and orders.

```bash
pip install -r requirements.txt
```

Create a `.env` file with:

```
NEON_DATABASE_URL=postgresql://USER:PASSWORD@HOST/DB?sslmode=require
```

DB service: [https://console.neon.tech/](https://console.neon.tech/)

Apply schema and sample data from `order.sql` in the Neon SQL editor.

Start the server:

```bash
uvicorn neon_dbOrderAPI:app --reload --port 8000
```

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Health

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Returns `{"status": "healthy"}` |

---

## Customers

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/customers` | List all customers (`ORDER BY customer_id`) |
| GET | `/customer/{customer_id}` | Get one customer by id |

**GET `/customer/{customer_id}` response fields:** `customer_id`, `name`, `email`, `phone`, `address`, `created_at`

- `404` if customer does not exist
- `500` on database errors

---

## Products

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/products` | List all products (`ORDER BY product_id`) |
| GET | `/products/{product_id}` | Get one product by id |
| POST | `/product` | Create a product |

**GET `/products/{product_id}` response fields:** `product_id`, `product_name`, `description`, `price`, `stock_quantity`, `is_active`

### POST `/product` body (`ProductCreate`)

```json
{
  "product_name": "Laptop",
  "description": "Business laptop",
  "price": 850.00,
  "stock_quantity": 10,
  "is_active": true
}
```

| Field | Rules |
| ----- | ----- |
| `product_name` | required, 1–150 characters |
| `description` | optional |
| `price` | required, `>= 0`, max 12 digits / 2 decimal places |
| `stock_quantity` | optional, default `0`, `>= 0` |
| `is_active` | optional, default `true` |

Success: `{"message": "Product created successfully"}`

---

## Orders

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/orders` | Create an order (`201`) |
| GET | `/orders` | List all orders (`ORDER BY order_id`) |
| GET | `/orders/{order_id}` | Get one order by id |
| PUT | `/orders/{order_id}/status` | Update order status only |

Allowed `status` values: `PENDING`, `CONFIRMED`, `SHIPPED`, `DELIVERED`, `CANCELLED`

### POST `/orders` body (`OrderCreate`)

```json
{
  "customer_id": 1,
  "product_id": 2,
  "order_quantity": 3,
  "status": "PENDING"
}
```

| Field | Rules |
| ----- | ----- |
| `customer_id` | required, `> 0` |
| `product_id` | required, `> 0` |
| `order_quantity` | required, `> 0` |
| `status` | optional, default `PENDING` |
| `total_amount` | optional in request; **server recalculates** as `product.price * order_quantity` |

Create-order checks before insert:

1. Customer exists (`404` Customer not found)
2. Product exists (`404` Product not found)
3. Stock is enough (`400` Insufficient stock)

Returns the inserted order row (`RETURNING *`).

### PUT `/orders/{order_id}/status` body (`OrderStatusUpdate`)

```json
{
  "status": "SHIPPED"
}
```

- `404` if order does not exist
- Returns the updated order row

---

## PUT vs PATCH (FastAPI)

- **PUT** expects the defined schema for that operation and replaces those fields. This API uses PUT for status: body is `{ "status": "..." }` and updates that field.
- **PATCH** is for partial updates (only send the fields you want to change). This project does not expose a PATCH endpoint yet.

---

## Error responses

| Status | When |
| ------ | ---- |
| `400` | Insufficient stock (create order) |
| `404` | Customer, product, or order not found |
| `422` | Request body fails Pydantic validation |
| `500` | Database or unexpected server error |
