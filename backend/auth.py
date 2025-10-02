from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity
)
from backend.models import User

# Initialize JWT globally
jwt = JWTManager()

def init_jwt(app):
    """Initialize JWT with Flask app"""
    jwt.init_app(app)

# ------------------------------
# Decorators
# ------------------------------
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ------------------------------
# Authentication Utilities
# ------------------------------
def authenticate_user(username, password):
    """
    Authenticate user and return access token
    Returns dict: {'access_token': ..., 'user': {...}} or None
    """
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return {
            'access_token': access_token,
            'user': user.to_dict()
        }
    return None

def get_current_user():
    """
    Get the currently authenticated user from JWT token
    Returns User object or None
    """
    try:
        current_user_id = get_jwt_identity()
        return User.query.get(current_user_id)
    except:
        return None
