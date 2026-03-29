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
