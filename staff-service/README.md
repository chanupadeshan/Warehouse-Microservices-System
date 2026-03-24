# Staff Service (FastAPI + SQLite)

This microservice manages warehouse staff records with full CRUD operations.

## Tech Stack

- FastAPI
- SQLite
- SQLAlchemy

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the service (from `staff-service` folder):

```bash
uvicorn app.main:app --reload --port 8005
```

## API Endpoints

- `POST /staff` - Create a staff member
- `GET /staff` - List all staff members
- `GET /staff/{staff_id}` - Get one staff member
- `PUT /staff/{staff_id}` - Update a staff member
- `DELETE /staff/{staff_id}` - Delete a staff member

## Sample Create Payload

```json
{
	"first_name": "Nimal",
	"last_name": "Perera",
	"email": "nimal.perera@warehouse.com",
	"phone": "+94-77-123-4567",
	"role": "Supervisor",
	"department": "Operations",
	"is_active": true
}
```
