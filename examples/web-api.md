# Task: Build a REST API

Create a Flask REST API with user management capabilities.

## Requirements

- [x] Flask application structure
- [x] User model with id, name, email
- [x] CRUD endpoints:
  - GET /users - List all users
  - GET /users/<id> - Get specific user
  - POST /users - Create new user
  - PUT /users/<id> - Update user
  - DELETE /users/<id> - Delete user
- [x] Input validation
- [x] Error handling
- [x] Unit tests
- [x] Documentation

## Technical Specifications

- Use Flask 2.0+
- SQLite for data storage
- Return JSON responses
- Proper HTTP status codes
- RESTful design principles

## Success Criteria

- All endpoints functional
- Tests pass
- Handles edge cases
- Clear error messages

## Implementation

The Flask REST API has been implemented in `examples/flask-api/`:

- **app.py** - Main application with User model, CRUD endpoints, validation, and error handling
- **test_app.py** - Comprehensive test suite with 26 tests covering all endpoints and edge cases
- **requirements.txt** - Dependencies (Flask, Flask-SQLAlchemy, pytest)
- **README.md** - Full API documentation with examples

### Test Results

All 26 tests pass:
- Index endpoint tests
- GET /users (empty, with data, multiple users)
- GET /users/<id> (found, not found)
- POST /users (success, missing fields, invalid email, duplicate email, empty body, name too long)
- PUT /users (update name, email, both, not found, duplicate email, invalid email)
- DELETE /users (success, not found)
- User model tests
- Edge cases (email normalization, whitespace trimming, empty name validation)

<!-- The orchestrator will continue iterations until all requirements are met -->
