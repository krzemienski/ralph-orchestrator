"""
Unit tests for Flask REST API User Management.

Tests all CRUD operations, input validation, and error handling.
"""

import pytest
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User


@pytest.fixture
def client():
    """Create a test client with a temporary database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


@pytest.fixture
def sample_user(client):
    """Create a sample user for testing."""
    response = client.post(
        '/users',
        data=json.dumps({'name': 'John Doe', 'email': 'john@example.com'}),
        content_type='application/json'
    )
    return json.loads(response.data)


class TestIndexEndpoint:
    """Tests for the root endpoint."""

    def test_index_returns_api_info(self, client):
        """Test that the index endpoint returns API information."""
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'User Management API'
        assert 'version' in data
        assert 'endpoints' in data


class TestGetUsers:
    """Tests for GET /users endpoint."""

    def test_get_users_empty(self, client):
        """Test getting users when database is empty."""
        response = client.get('/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['users'] == []
        assert data['count'] == 0

    def test_get_users_with_data(self, client, sample_user):
        """Test getting users when users exist."""
        response = client.get('/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1
        assert len(data['users']) == 1
        assert data['users'][0]['name'] == 'John Doe'

    def test_get_users_multiple(self, client):
        """Test getting multiple users."""
        # Create multiple users
        for i in range(3):
            client.post(
                '/users',
                data=json.dumps({'name': f'User {i}', 'email': f'user{i}@example.com'}),
                content_type='application/json'
            )

        response = client.get('/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 3


class TestGetUser:
    """Tests for GET /users/<id> endpoint."""

    def test_get_user_exists(self, client, sample_user):
        """Test getting an existing user."""
        user_id = sample_user['id']
        response = client.get(f'/users/{user_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == user_id
        assert data['name'] == 'John Doe'
        assert data['email'] == 'john@example.com'

    def test_get_user_not_found(self, client):
        """Test getting a non-existent user returns 404."""
        response = client.get('/users/9999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Not Found' in data['error']


class TestCreateUser:
    """Tests for POST /users endpoint."""

    def test_create_user_success(self, client):
        """Test creating a valid user."""
        response = client.post(
            '/users',
            data=json.dumps({'name': 'Jane Doe', 'email': 'jane@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Jane Doe'
        assert data['email'] == 'jane@example.com'
        assert 'id' in data
        assert 'created_at' in data

    def test_create_user_missing_name(self, client):
        """Test creating user without name returns 400."""
        response = client.post(
            '/users',
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Name is required' in data['messages']

    def test_create_user_missing_email(self, client):
        """Test creating user without email returns 400."""
        response = client.post(
            '/users',
            data=json.dumps({'name': 'Test User'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Email is required' in data['messages']

    def test_create_user_invalid_email(self, client):
        """Test creating user with invalid email returns 400."""
        response = client.post(
            '/users',
            data=json.dumps({'name': 'Test', 'email': 'invalid-email'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid email format' in data['messages']

    def test_create_user_duplicate_email(self, client, sample_user):
        """Test creating user with duplicate email returns 409."""
        response = client.post(
            '/users',
            data=json.dumps({'name': 'Another John', 'email': 'john@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'Conflict' in data['error']

    def test_create_user_empty_body(self, client):
        """Test creating user with empty body returns 400."""
        response = client.post(
            '/users',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_create_user_name_too_long(self, client):
        """Test creating user with name exceeding max length returns 400."""
        response = client.post(
            '/users',
            data=json.dumps({'name': 'x' * 101, 'email': 'test@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Name must be 100 characters or less' in data['messages']


class TestUpdateUser:
    """Tests for PUT /users/<id> endpoint."""

    def test_update_user_name(self, client, sample_user):
        """Test updating user's name."""
        user_id = sample_user['id']
        response = client.put(
            f'/users/{user_id}',
            data=json.dumps({'name': 'John Updated'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'John Updated'
        assert data['email'] == 'john@example.com'  # Email unchanged

    def test_update_user_email(self, client, sample_user):
        """Test updating user's email."""
        user_id = sample_user['id']
        response = client.put(
            f'/users/{user_id}',
            data=json.dumps({'email': 'john.updated@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['email'] == 'john.updated@example.com'
        assert data['name'] == 'John Doe'  # Name unchanged

    def test_update_user_both_fields(self, client, sample_user):
        """Test updating both name and email."""
        user_id = sample_user['id']
        response = client.put(
            f'/users/{user_id}',
            data=json.dumps({'name': 'Jane Doe', 'email': 'jane@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Jane Doe'
        assert data['email'] == 'jane@example.com'

    def test_update_user_not_found(self, client):
        """Test updating non-existent user returns 404."""
        response = client.put(
            '/users/9999',
            data=json.dumps({'name': 'Test'}),
            content_type='application/json'
        )
        assert response.status_code == 404

    def test_update_user_duplicate_email(self, client, sample_user):
        """Test updating user to duplicate email returns 409."""
        # Create another user
        client.post(
            '/users',
            data=json.dumps({'name': 'Jane', 'email': 'jane@example.com'}),
            content_type='application/json'
        )

        # Try to update first user's email to second user's email
        user_id = sample_user['id']
        response = client.put(
            f'/users/{user_id}',
            data=json.dumps({'email': 'jane@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 409

    def test_update_user_invalid_email(self, client, sample_user):
        """Test updating user with invalid email returns 400."""
        user_id = sample_user['id']
        response = client.put(
            f'/users/{user_id}',
            data=json.dumps({'email': 'not-an-email'}),
            content_type='application/json'
        )
        assert response.status_code == 400


class TestDeleteUser:
    """Tests for DELETE /users/<id> endpoint."""

    def test_delete_user_success(self, client, sample_user):
        """Test deleting an existing user."""
        user_id = sample_user['id']
        response = client.delete(f'/users/{user_id}')
        assert response.status_code == 204

        # Verify user is deleted
        response = client.get(f'/users/{user_id}')
        assert response.status_code == 404

    def test_delete_user_not_found(self, client):
        """Test deleting non-existent user returns 404."""
        response = client.delete('/users/9999')
        assert response.status_code == 404


class TestUserModel:
    """Tests for the User model."""

    def test_user_to_dict(self, client):
        """Test User model's to_dict method."""
        with app.app_context():
            user = User(name='Test User', email='test@example.com')
            db.session.add(user)
            db.session.commit()

            user_dict = user.to_dict()
            assert user_dict['name'] == 'Test User'
            assert user_dict['email'] == 'test@example.com'
            assert 'id' in user_dict
            assert 'created_at' in user_dict
            assert 'updated_at' in user_dict

    def test_user_repr(self, client):
        """Test User model's __repr__ method."""
        with app.app_context():
            user = User(name='Test User', email='test@example.com')
            assert repr(user) == '<User Test User>'


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_email_normalization(self, client):
        """Test that emails are normalized to lowercase."""
        response = client.post(
            '/users',
            data=json.dumps({'name': 'Test', 'email': 'TEST@EXAMPLE.COM'}),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['email'] == 'test@example.com'

    def test_name_whitespace_trimmed(self, client):
        """Test that name whitespace is trimmed."""
        response = client.post(
            '/users',
            data=json.dumps({'name': '  Test User  ', 'email': 'test@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Test User'

    def test_empty_name_validation(self, client):
        """Test that empty/whitespace-only name is rejected."""
        response = client.post(
            '/users',
            data=json.dumps({'name': '   ', 'email': 'test@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
