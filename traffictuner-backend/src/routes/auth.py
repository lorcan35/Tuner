from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re

from src.models.user import db, User
from src.models.subscription import Subscription

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create new user
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role='USER',
            credits=3,  # Free trial credits
            is_new_user=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(
            identity=user.user_id,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint with rate limiting"""
    try:
        # Get security instance from app
        security = getattr(current_app, 'security', None)
        
        # Check rate limiting if security is available
        if security:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if security.is_ip_blocked(ip_address):
                return jsonify({
                    'error': 'Too many failed attempts. Please try again later.',
                    'retry_after': 900  # 15 minutes in seconds
                }), 429
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            # Record failed attempt if security is available
            if security:
                ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                blocked = security.record_failed_attempt(ip_address)
                if blocked:
                    return jsonify({
                        'error': 'Too many failed attempts. Account temporarily locked.',
                        'retry_after': 900
                    }), 429
            
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Successful login - clear failed attempts
        if security:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            security.clear_failed_attempts(ip_address)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(
            identity=user.user_id,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Include subscription information
        user_data = user.to_dict()
        if user.subscription:
            user_data['subscription'] = user.subscription.to_dict()
        
        return jsonify({'user': user_data}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user information', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name'].strip()
        
        if 'bio' in data:
            user.bio = data['bio']
        
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']
        
        if 'is_new_user' in data:
            user.is_new_user = data['is_new_user']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Verify current password
        if not check_password_hash(user.password_hash, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to change password', 'details': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    # In a more sophisticated implementation, you would blacklist the token
    # For now, we'll just return a success message
    return jsonify({'message': 'Logout successful'}), 200

# OAuth endpoints (placeholder for future implementation)
@auth_bp.route('/oauth/google', methods=['POST'])
def google_oauth():
    """Google OAuth login"""
    # TODO: Implement Google OAuth
    return jsonify({'error': 'Google OAuth not implemented yet'}), 501

@auth_bp.route('/oauth/github', methods=['POST'])
def github_oauth():
    """GitHub OAuth login"""
    # TODO: Implement GitHub OAuth
    return jsonify({'error': 'GitHub OAuth not implemented yet'}), 501

# Password reset endpoints (placeholder for future implementation)
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Initiate password reset"""
    # TODO: Implement password reset
    return jsonify({'error': 'Password reset not implemented yet'}), 501

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    # TODO: Implement password reset
    return jsonify({'error': 'Password reset not implemented yet'}), 501

