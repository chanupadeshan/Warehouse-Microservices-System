# Supplier Service (Warehouse Microservices System)

Supplier Service is a FastAPI microservice responsible for managing supplier/vendor information in the warehouse system.

## Tech Stack

- Python
- FastAPI
- SQLite
- SQLAlchemy ORM
- Pydantic (request/response validation)

## Features

- Create a new supplier
- Get all suppliers
- Get supplier by ID
- Update supplier details
- Delete supplier **only when** `contract_status` is `Inactive`
- Swagger UI included (FastAPI default docs)
- Email format validation
- Error handling for "Supplier not found"

## Supplier Fields

- `id`
- `supplier_name`
- `company_name`
- `email`
- `phone`
- `address`
- `contract_status` ("Active" | "Inactive")
- `created_at`
- `updated_at`

## Project Structure

```
supplier-service/
	requirements.txt
	README.md
	app/
		__init__.py
		main.py
		database.py
		deps.py
		models.py
		schemas.py
		crud.py
		routes/
			__init__.py
			suppliers.py
```

## Setup & Run (Windows)

From the `supplier-service` folder:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open:

- Health check: http://127.0.0.1:8000/
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Database Location

By default, the service creates a SQLite file named `supplier.db` in the `supplier-service` folder.

### Optional: Configure Database URL

You can override the database using an environment variable:

- `SUPPLIER_DATABASE_URL` (default: `sqlite:///./supplier.db`)

Example (PowerShell):

```powershell
$env:SUPPLIER_DATABASE_URL = "sqlite:///./supplier.db"
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

Base path is RESTful and clean for API Gateway integration.

- `POST /suppliers` - Create supplier
- `GET /suppliers` - Get all suppliers
- `GET /suppliers/{id}` - Get supplier by ID
- `PUT /suppliers/{id}` - Update supplier
- `DELETE /suppliers/{id}` - Delete supplier (only if `contract_status` is `Inactive`)

## Example Requests / Responses

### 1) Create Supplier (POST /suppliers)

Request body:

```json
{
	"supplier_name": "John Supplier",
	"company_name": "ABC Supplies Ltd",
	"email": "john@abc.com",
	"phone": "+94 77 123 4567",
	"address": "Colombo, Sri Lanka",
	"contract_status": "Active"
}
```

Response (201 Created):

```json
{
	"supplier_name": "John Supplier",
	"company_name": "ABC Supplies Ltd",
	"email": "john@abc.com",
	"phone": "+94 77 123 4567",
	"address": "Colombo, Sri Lanka",
	"contract_status": "Active",
	"id": 1,
	"created_at": "2026-03-25T10:20:30.123456",
	"updated_at": "2026-03-25T10:20:30.123456"
}
```

### 2) Get All Suppliers (GET /suppliers)

Response (200 OK):

```json
[
	{
		"supplier_name": "John Supplier",
		"company_name": "ABC Supplies Ltd",
		"email": "john@abc.com",
		"phone": "+94 77 123 4567",
		"address": "Colombo, Sri Lanka",
		"contract_status": "Active",
		"id": 1,
		"created_at": "2026-03-25T10:20:30.123456",
		"updated_at": "2026-03-25T10:20:30.123456"
	}
]
```

### 3) Get Supplier by ID (GET /suppliers/1)

- If the supplier does not exist, the API returns `404` with:

```json
{"detail": "Supplier not found"}
```

### 4) Update Supplier (PUT /suppliers/1)

Request body (update only what you need):

```json
{
	"contract_status": "Inactive"
}
```

### 5) Delete Supplier (DELETE /suppliers/1)

Delete rule (assignment requirement):

- If `contract_status` is `Inactive` → delete is allowed
- If `contract_status` is `Active` → API returns `409 Conflict`

Success response:

```json
{"detail": "Supplier deleted"}
```

Conflict response:

```json
{"detail": "Supplier can only be deleted when contract_status is 'Inactive'"}
```

## How to Test Using Swagger UI

1. Run the service with `uvicorn app.main:app --reload --port 8000`
2. Open http://127.0.0.1:8000/docs
3. Expand the `suppliers` section
4. Click **Try it out** and test:
	 - `POST /suppliers` to create
	 - `GET /suppliers` to list
	 - `GET /suppliers/{id}` to read
	 - `PUT /suppliers/{id}` to update
	 - `DELETE /suppliers/{id}` to delete (only inactive)

## File-by-File Explanation

- `app/main.py`: FastAPI application entry point, registers routes, creates DB tables
- `app/database.py`: SQLAlchemy engine/session setup for SQLite
- `app/deps.py`: `get_db()` dependency (opens and closes DB session per request)
- `app/models.py`: SQLAlchemy `Supplier` model (database table definition)
- `app/schemas.py`: Pydantic schemas (validation + response models). Email uses `EmailStr`
- `app/crud.py`: CRUD/service functions that talk to the database
- `app/routes/suppliers.py`: REST API endpoints for suppliers
- `__init__.py` files: package markers (kept empty) to make imports reliable
