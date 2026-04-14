# IS601 Module 11 – Calculation Model with Factory Pattern

This module extends the FastAPI application from Module 10 by adding a structured `Calculation` model with Pydantic validation and a factory pattern for arithmetic operations.

## What's New in Module 11

- **Calculation Model** (`id`, `a`, `b`, `type`, `result`, `timestamp`, `user_id`) using SQLAlchemy
- **OperationType Enum** – restricts `type` to `Add`, `Sub`, `Multiply`, `Divide`
- **CalculationFactory** – selects and runs the correct operation class at creation time
- **Pydantic Validation** – rejects invalid operation types and division by zero
- **Full test suite** – unit tests for operations/factory/schemas, integration tests for DB correctness and error cases

## Project Structure

```
IS601_Module11/
├── app/
│   ├── calculator.py   # OperationType enum + operation classes + CalculationFactory
│   ├── models.py       # SQLAlchemy User and Calculation models
│   ├── schemas.py      # Pydantic schemas with validation
│   ├── main.py         # FastAPI routes
│   ├── database.py     # DB engine and session
│   └── auth.py         # Password hashing utilities
├── tests/
│   ├── conftest.py
│   ├── test_unit.py
│   └── test_integration.py
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Running Tests Locally

### Option 1 – SQLite (no Docker needed)

```bash
pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Option 2 – PostgreSQL via Docker Compose

```bash
docker-compose up -d db
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db pytest tests/ -v
```

## Running the Application

```bash
docker-compose up --build
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050 (admin@admin.com / admin)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/users/` | Create user |
| GET | `/users/` | List users |
| GET | `/users/{id}` | Get user |
| DELETE | `/users/{id}` | Delete user |
| POST | `/calculations/` | Create calculation |
| GET | `/calculations/` | List calculations |
| GET | `/calculations/{id}` | Get calculation |
| DELETE | `/calculations/{id}` | Delete calculation |
| GET | `/calculations/join/all` | Calculations with user info |
| GET | `/health` | Health check |

### Example – Create a calculation

```json
POST /calculations/
{
  "a": 10,
  "b": 4,
  "type": "Add",
  "user_id": 1
}
```

Response:
```json
{
  "id": 1,
  "a": 10.0,
  "b": 4.0,
  "type": "Add",
  "result": 14.0,
  "timestamp": "2024-01-01T00:00:00",
  "user_id": 1
}
```

## Docker Hub

Docker image: [kushyarwar/is601-module11](https://hub.docker.com/r/kushyarwar/is601-module11)

```bash
docker pull kushyarwar/is601-module11:latest
```

## CI/CD Screenshots

### GitHub Actions – Successful Workflow Run
![GitHub Actions](Screenshots/github%20actions.png)

### Docker Hub – Image Successfully Pushed
![Docker Hub](Screenshots/docker.png)
