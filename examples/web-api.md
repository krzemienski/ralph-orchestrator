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

## Completion Status

**Status: COMPLETE** ✅

### Final Verification (2026-01-10 17:50 EST)

All 26 tests pass:
```
test_app.py::TestIndexEndpoint::test_index_returns_api_info PASSED
test_app.py::TestGetUsers::test_get_users_empty PASSED
test_app.py::TestGetUsers::test_get_users_with_data PASSED
test_app.py::TestGetUsers::test_get_users_multiple PASSED
test_app.py::TestGetUser::test_get_user_exists PASSED
test_app.py::TestGetUser::test_get_user_not_found PASSED
test_app.py::TestCreateUser::test_create_user_success PASSED
test_app.py::TestCreateUser::test_create_user_missing_name PASSED
test_app.py::TestCreateUser::test_create_user_missing_email PASSED
test_app.py::TestCreateUser::test_create_user_invalid_email PASSED
test_app.py::TestCreateUser::test_create_user_duplicate_email PASSED
test_app.py::TestCreateUser::test_create_user_empty_body PASSED
test_app.py::TestCreateUser::test_create_user_name_too_long PASSED
test_app.py::TestUpdateUser::test_update_user_name PASSED
test_app.py::TestUpdateUser::test_update_user_email PASSED
test_app.py::TestUpdateUser::test_update_user_both_fields PASSED
test_app.py::TestUpdateUser::test_update_user_not_found PASSED
test_app.py::TestUpdateUser::test_update_user_duplicate_email PASSED
test_app.py::TestUpdateUser::test_update_user_invalid_email PASSED
test_app.py::TestDeleteUser::test_delete_user_success PASSED
test_app.py::TestDeleteUser::test_delete_user_not_found PASSED
test_app.py::TestUserModel::test_user_to_dict PASSED
test_app.py::TestUserModel::test_user_repr PASSED
test_app.py::TestEdgeCases::test_email_normalization PASSED
test_app.py::TestEdgeCases::test_name_whitespace_trimmed PASSED
test_app.py::TestEdgeCases::test_empty_name_validation PASSED

26 passed in 0.29s
```

All requirements implemented:
- Flask application structure with SQLite ✅
- User model with id, name, email ✅
- All 5 CRUD endpoints functional ✅
- Input validation (email format, name length, required fields) ✅
- Error handling with proper HTTP status codes ✅
- 26 comprehensive unit tests ✅
- Full API documentation with curl examples ✅

**No further iterations needed.**
