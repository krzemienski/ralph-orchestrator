"""
Flask REST API for User Management

A simple REST API with CRUD operations for managing users.
Uses SQLite for data storage and returns JSON responses.
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "users.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)


class User(db.Model):
    """User model representing a user in the system."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert User object to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<User {self.name}>'


# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    return jsonify({
        'error': 'Bad Request',
        'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
    }), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404


@app.errorhandler(409)
def conflict(error):
    """Handle 409 Conflict errors."""
    return jsonify({
        'error': 'Conflict',
        'message': str(error.description) if hasattr(error, 'description') else 'Resource conflict'
    }), 409


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    db.session.rollback()
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


# Input Validation Helper
def validate_user_data(data, require_all=True):
    """
    Validate user input data.

    Args:
        data: Dictionary containing user data
        require_all: If True, requires both name and email; if False, at least one

    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []

    if data is None:
        return False, ['Request body is required']

    name = data.get('name')
    email = data.get('email')

    if require_all:
        if not name:
            errors.append('Name is required')
        if not email:
            errors.append('Email is required')
    else:
        if not name and not email:
            errors.append('At least one field (name or email) is required for update')

    # Validate name if provided
    if name is not None:
        if not isinstance(name, str):
            errors.append('Name must be a string')
        elif len(name.strip()) == 0:
            errors.append('Name cannot be empty')
        elif len(name) > 100:
            errors.append('Name must be 100 characters or less')

    # Validate email if provided
    if email is not None:
        if not isinstance(email, str):
            errors.append('Email must be a string')
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors.append('Invalid email format')
        elif len(email) > 120:
            errors.append('Email must be 120 characters or less')

    return len(errors) == 0, errors


# API Endpoints
@app.route('/users', methods=['GET'])
def get_users():
    """
    Get all users.

    Returns:
        JSON array of all users with 200 OK status
    """
    users = User.query.all()
    return jsonify({
        'users': [user.to_dict() for user in users],
        'count': len(users)
    }), 200


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a specific user by ID.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        JSON object of the user with 200 OK status
        404 Not Found if user doesn't exist
    """
    user = User.query.get(user_id)
    if user is None:
        return jsonify({
            'error': 'Not Found',
            'message': f'User with id {user_id} not found'
        }), 404
    return jsonify(user.to_dict()), 200


@app.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user.

    Request Body:
        name: User's name (required, string, max 100 chars)
        email: User's email (required, string, valid email format, max 120 chars)

    Returns:
        JSON object of created user with 201 Created status
        400 Bad Request if validation fails
        409 Conflict if email already exists
    """
    data = request.get_json()

    # Validate input
    is_valid, errors = validate_user_data(data, require_all=True)
    if not is_valid:
        return jsonify({
            'error': 'Validation Error',
            'messages': errors
        }), 400

    # Check for duplicate email
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'error': 'Conflict',
            'message': f"Email '{data['email']}' already exists"
        }), 409

    # Create new user
    user = User(
        name=data['name'].strip(),
        email=data['email'].strip().lower()
    )

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update an existing user.

    Args:
        user_id: The ID of the user to update

    Request Body:
        name: User's name (optional, string, max 100 chars)
        email: User's email (optional, string, valid email format, max 120 chars)

    Returns:
        JSON object of updated user with 200 OK status
        400 Bad Request if validation fails
        404 Not Found if user doesn't exist
        409 Conflict if email already exists for another user
    """
    user = User.query.get(user_id)
    if user is None:
        return jsonify({
            'error': 'Not Found',
            'message': f'User with id {user_id} not found'
        }), 404

    data = request.get_json()

    # Validate input
    is_valid, errors = validate_user_data(data, require_all=False)
    if not is_valid:
        return jsonify({
            'error': 'Validation Error',
            'messages': errors
        }), 400

    # Check for duplicate email if email is being updated
    if 'email' in data and data['email']:
        email = data['email'].strip().lower()
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({
                'error': 'Conflict',
                'message': f"Email '{email}' already exists"
            }), 409
        user.email = email

    # Update name if provided
    if 'name' in data and data['name']:
        user.name = data['name'].strip()

    db.session.commit()

    return jsonify(user.to_dict()), 200


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user.

    Args:
        user_id: The ID of the user to delete

    Returns:
        Empty response with 204 No Content status
        404 Not Found if user doesn't exist
    """
    user = User.query.get(user_id)
    if user is None:
        return jsonify({
            'error': 'Not Found',
            'message': f'User with id {user_id} not found'
        }), 404

    db.session.delete(user)
    db.session.commit()

    return '', 204


@app.route('/', methods=['GET'])
def index():
    """API root endpoint with basic info."""
    return jsonify({
        'name': 'User Management API',
        'version': '1.0.0',
        'endpoints': {
            'GET /users': 'List all users',
            'GET /users/<id>': 'Get a specific user',
            'POST /users': 'Create a new user',
            'PUT /users/<id>': 'Update a user',
            'DELETE /users/<id>': 'Delete a user'
        }
    }), 200


if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
