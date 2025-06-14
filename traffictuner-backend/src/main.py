import os
import sys
from datetime import datetime, timedelta
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Import models
from src.models.user import db, User
from src.models.domain import Domain
from src.models.analysis_report import AnalysisReport
from src.models.subscription import Subscription
from src.models.llm_config import LLMConfig
from src.models.tracking_config import TrackingConfig

# Import routes
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.domains import domains_bp
from src.routes.analysis import analysis_bp
from src.routes.admin import admin_bp
from src.routes.billing import billing_bp
from src.routes.tracking import tracking_bp

# Import services
from src.services.analysis_worker import init_worker
from src.security_enhancements import init_security
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'traffictuner-super-secret-key-2025')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-traffictuner')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS configuration for frontend integration
CORS(app, origins=["http://localhost:5173", "http://localhost:3000", "*"])

# Initialize JWT
jwt = JWTManager(app)

# # Register blueprints
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(domains_bp, url_prefix='/api/domains')
app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(billing_bp, url_prefix='/api/billing')
app.register_blueprint(tracking_bp, url_prefix='/api/tracking')
# Initialize database
db.init_app(app)

# Initialize security enhancements
security = init_security(app)
app.security = security

@app.before_request
def create_tables():
    """Create database tables and seed initial data"""
    if not hasattr(create_tables, 'initialized'):
        db.create_all()
        
        # Create super admin user if it doesn't exist
        super_admin = User.query.filter_by(email='admin@traffictuner.com').first()
        if not super_admin:
            super_admin = User(
                name='Super Admin',
                email='admin@traffictuner.com',
                password_hash=generate_password_hash('admin123'),
                role='SUPER_ADMIN',
                credits=1000,
                is_new_user=False
            )
            db.session.add(super_admin)
            db.session.commit()
            print("Super admin user created: admin@traffictuner.com / admin123")
        
        create_tables.initialized = True

# Initialize background worker
worker = init_worker(app)

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# Serve static files (for frontend integration)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({'message': 'TrafficTuner API is running'}), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token is required'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)

