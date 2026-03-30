# Microservice-fastapi

## Database Layout

The stack uses one PostgreSQL container, but each service gets its own database:

- `cargo-service` -> `cargo_db`
- `location-service` -> `location_db`
- `inventory-service` -> `inventory_db`
- `supplier-service` -> `supplier_db`
- `staff-service` -> `staff_db`
- `equipment-service` -> `equipment_db`

`docker compose` starts a short-lived `postgres-init` container that creates any missing service databases before the application containers start.

## Running The Stack

```bash
cp .env.example .env
docker compose up --build
```

## Windows Note (Line Endings)

If `postgres-init` fails with an error like `set: line 2: illegal option -`, a shell script was likely checked out with CRLF line endings.

This repository includes a `.gitattributes` rule (`*.sh text eol=lf`) to keep shell scripts in Unix LF format, which is required by the Alpine `/bin/sh` used in containers.

If you already cloned before this rule was added, re-checkout shell files with LF and run the stack again.

## API Endpoints

All services are available through the API Gateway on port `8080`.

### API Gateway (`http://localhost:8080`)

- `GET /` - Gateway metadata
- `GET /health` - Gateway + downstream service health summary
- `GET /docs` - Gateway Swagger UI
- `GET /openapi.json` - Gateway OpenAPI schema
- `GET /services/docs` - Index of docs URLs exposed via gateway
- `GET /{service}/docs` - Swagger UI for a specific microservice via gateway (`service`: `cargo`, `location`, `inventory`, `supplier`, `staff`, `equipment`)
- `GET /{service}/openapi.json` - OpenAPI schema for a specific microservice via gateway
- `GET|POST|PUT|PATCH|DELETE /{service}` - Proxy to service collection route
- `GET|POST|PUT|PATCH|DELETE /{service}/{path}` - Proxy to nested resource route

### Cargo Service

- `GET /` - Service metadata
- `GET /health` - Health check
- `POST /cargo` - Create cargo shipment
- `POST /cargo/intake` - Create shipment using intake workflow
- `GET /cargo` - List cargo shipments
- `GET /cargo/{cargo_id}` - Get one cargo shipment
- `PUT /cargo/{cargo_id}` - Update cargo shipment
- `DELETE /cargo/{cargo_id}` - Delete cargo shipment

### Location Service

- `GET /` - Service metadata
- `GET /health` - Health check
- `POST /locations` - Create location
- `GET /locations` - List locations
- `GET /locations/{location_id}` - Get one location
- `POST /locations/reserve` - Reserve a location
- `PUT /locations/{location_id}` - Update location
- `POST /locations/{location_id}/release` - Release location
- `DELETE /locations/{location_id}` - Delete location

### Inventory Service

- `GET /` - Service metadata
- `GET /health` - Health check
- `POST /inventory-items` - Create inventory item
- `GET /inventory-items` - List inventory items
- `GET /inventory-items/{item_id}` - Get one inventory item
- `POST /inventory/receive` - Receive inventory (alias)
- `POST /inventory-items/receive` - Receive inventory
- `POST /inventory/release` - Release inventory (alias)
- `POST /inventory-items/release` - Release inventory
- `PUT /inventory-items/{item_id}` - Update inventory item
- `DELETE /inventory-items/{item_id}` - Delete inventory item

### Supplier Service

- `GET /` - Service metadata
- `GET /health` - Health check
- `POST /suppliers` - Create supplier
- `GET /suppliers` - List suppliers
- `GET /suppliers/{supplier_id}` - Get one supplier
- `GET /suppliers/{supplier_id}/validate` - Validate supplier status
- `PUT /suppliers/{supplier_id}` - Update supplier
- `DELETE /suppliers/{supplier_id}` - Delete supplier

### Staff Service

- `GET /` - Service status
- `GET /health` - Health check
- `POST /staff` - Create staff member
- `GET /staff` - List staff members
- `GET /staff/{staff_id}` - Get one staff member
- `POST /staff/assign` - Assign available staff member to task
- `PUT /staff/{staff_id}` - Update staff member
- `POST /staff/{staff_id}/release` - Release assigned task from staff member
- `DELETE /staff/{staff_id}` - Delete staff member

### Equipment Service

- `GET /` - Service metadata
- `GET /health` - Health check
- `POST /equipment` - Create equipment
- `GET /equipment` - List equipment
- `GET /equipment/{equipment_id}` - Get one equipment record
- `POST /equipment/assign` - Assign equipment
- `PUT /equipment/{equipment_id}` - Update equipment
- `POST /equipment/{equipment_id}/release` - Release equipment
- `DELETE /equipment/{equipment_id}` - Delete equipment

## Folder Structure

```text
Warehouse-Microservices-System/
├── README.md
├── api-gateway/
│   ├── README.md
│   ├── main.py
│   └── requirements.txt
├── cargo-service/
│   ├── README.md
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   └── requirements.txt
├── equipment-service/
│   ├── README.md
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   └── requirements.txt
├── inventory-service/
│   ├── README.md
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   └── requirements.txt
├── location-service/
│   ├── README.md
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   └── requirements.txt
├── staff-service/
│   ├── README.md
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   └── requirements.txt
└── supplier-service/
    ├── README.md
    ├── app/
    │   ├── database.py
    │   ├── main.py
    │   └── models.py
    └── requirements.txt
```
