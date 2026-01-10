# Flask REST API - User Management

A simple REST API for user management built with Flask 2.0+ and SQLite.

## Features

- Full CRUD operations for users
- Input validation with meaningful error messages
- Proper HTTP status codes
- RESTful design principles
- SQLite database for data persistence
- Comprehensive test suite

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the API

```bash
python app.py
```

The server will start at `http://localhost:5000`

## API Endpoints

### Root
- **GET /** - API information and available endpoints

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List all users |
| GET | `/users/<id>` | Get a specific user |
| POST | `/users` | Create a new user |
| PUT | `/users/<id>` | Update a user |
| DELETE | `/users/<id>` | Delete a user |

## Request/Response Examples

### Create User
```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-10T12:00:00",
  "updated_at": "2024-01-10T12:00:00"
}
```

### Get All Users
```bash
curl http://localhost:5000/users
```

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2024-01-10T12:00:00",
      "updated_at": "2024-01-10T12:00:00"
    }
  ],
  "count": 1
}
```

### Get Single User
```bash
curl http://localhost:5000/users/1
```

### Update User
```bash
curl -X PUT http://localhost:5000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "John Updated"}'
```

### Delete User
```bash
curl -X DELETE http://localhost:5000/users/1
```

**Response (204 No Content)**

## Error Responses

### Validation Error (400)
```json
{
  "error": "Validation Error",
  "messages": ["Name is required", "Invalid email format"]
}
```

### Not Found (404)
```json
{
  "error": "Not Found",
  "message": "User with id 99 not found"
}
```

### Conflict (409)
```json
{
  "error": "Conflict",
  "message": "Email 'john@example.com' already exists"
}
```

## Validation Rules

- **name**: Required, string, max 100 characters
- **email**: Required, valid email format, max 120 characters, unique

## Running Tests

```bash
# Run all tests
pytest test_app.py -v

# Run with coverage
pytest test_app.py --cov=app --cov-report=term-missing
```

## Project Structure

```
flask-api/
├── app.py           # Main application with routes and models
├── test_app.py      # Unit tests
├── requirements.txt # Dependencies
└── README.md        # This file
```

## Technical Details

- **Framework**: Flask 2.0+
- **Database**: SQLite (SQLAlchemy ORM)
- **Testing**: pytest
- **Python**: 3.8+
