from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.models.user import db, User
from src.models.llm_config import LLMConfig
from src.models.domain import Domain
from src.models.analysis_report import AnalysisReport
from src.models.subscription import Subscription

admin_bp = Blueprint('admin', __name__)

def require_admin():
    """Decorator to require admin role"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.filter_by(user_id=user_id).first()
            
            if not user or not user.is_admin():
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_admin()
def get_admin_dashboard():
    """Get admin dashboard statistics"""
    try:
        # Get user statistics
        total_users = User.query.count()
        new_users_today = User.query.filter(
            User.created_at >= datetime.utcnow().date()
        ).count()
        
        # Get domain statistics
        total_domains = Domain.query.count()
        active_domains = Domain.query.filter_by(status='active').count()
        
        # Get analysis statistics
        total_analyses = AnalysisReport.query.count()
        completed_analyses = AnalysisReport.query.filter_by(status='completed').count()
        pending_analyses = AnalysisReport.query.filter_by(status='pending').count()
        
        # Get subscription statistics
        active_subscriptions = Subscription.query.filter_by(status='active').count()
        
        # Get LLM usage statistics
        llm_configs = LLMConfig.query.filter_by(is_active=True).all()
        total_llm_requests = sum(config.total_requests for config in llm_configs)
        total_llm_cost = sum(config.total_cost for config in llm_configs)
        
        return jsonify({
            'users': {
                'total': total_users,
                'new_today': new_users_today
            },
            'domains': {
                'total': total_domains,
                'active': active_domains
            },
            'analyses': {
                'total': total_analyses,
                'completed': completed_analyses,
                'pending': pending_analyses
            },
            'subscriptions': {
                'active': active_subscriptions
            },
            'llm_usage': {
                'total_requests': total_llm_requests,
                'total_cost': total_llm_cost,
                'active_configs': len(llm_configs)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get dashboard data', 'details': str(e)}), 500

@admin_bp.route('/llm-configs', methods=['GET'])
@jwt_required()
@require_admin()
def get_llm_configs():
    """Get all LLM configurations"""
    try:
        configs = LLMConfig.query.order_by(LLMConfig.priority.desc()).all()
        
        return jsonify({
            'configs': [config.to_dict() for config in configs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get LLM configs', 'details': str(e)}), 500

@admin_bp.route('/llm-configs', methods=['POST'])
@jwt_required()
@require_admin()
def create_llm_config():
    """Create a new LLM configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['provider', 'name', 'model_name', 'api_key']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create new config
        config = LLMConfig(
            provider=data['provider'],
            name=data['name'],
            description=data.get('description'),
            model_name=data['model_name'],
            api_endpoint=data.get('api_endpoint'),
            priority=data.get('priority', 1),
            rate_limit_per_minute=data.get('rate_limit_per_minute', 60),
            cost_per_1k_tokens=data.get('cost_per_1k_tokens', 0.0),
            is_active=data.get('is_active', True)
        )
        
        # Set encrypted API key
        config.set_api_key(data['api_key'])
        
        # Set settings if provided
        if data.get('settings'):
            config.set_settings(data['settings'])
        
        db.session.add(config)
        db.session.commit()
        
        return jsonify({
            'message': 'LLM configuration created successfully',
            'config': config.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create LLM config', 'details': str(e)}), 500

@admin_bp.route('/llm-configs/<config_id>', methods=['GET'])
@jwt_required()
@require_admin()
def get_llm_config(config_id):
    """Get a specific LLM configuration"""
    try:
        config = LLMConfig.query.filter_by(config_id=config_id).first()
        
        if not config:
            return jsonify({'error': 'LLM config not found'}), 404
        
        return jsonify({
            'config': config.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get LLM config', 'details': str(e)}), 500

@admin_bp.route('/llm-configs/<config_id>', methods=['PATCH'])
@jwt_required()
@require_admin()
def update_llm_config(config_id):
    """Update an LLM configuration"""
    try:
        config = LLMConfig.query.filter_by(config_id=config_id).first()
        
        if not config:
            return jsonify({'error': 'LLM config not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            config.name = data['name']
        
        if 'description' in data:
            config.description = data['description']
        
        if 'model_name' in data:
            config.model_name = data['model_name']
        
        if 'api_endpoint' in data:
            config.api_endpoint = data['api_endpoint']
        
        if 'api_key' in data:
            config.set_api_key(data['api_key'])
        
        if 'priority' in data:
            config.priority = data['priority']
        
        if 'rate_limit_per_minute' in data:
            config.rate_limit_per_minute = data['rate_limit_per_minute']
        
        if 'cost_per_1k_tokens' in data:
            config.cost_per_1k_tokens = data['cost_per_1k_tokens']
        
        if 'is_active' in data:
            config.is_active = data['is_active']
        
        if 'settings' in data:
            config.set_settings(data['settings'])
        
        config.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'LLM configuration updated successfully',
            'config': config.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update LLM config', 'details': str(e)}), 500

@admin_bp.route('/llm-configs/<config_id>', methods=['DELETE'])
@jwt_required()
@require_admin()
def delete_llm_config(config_id):
    """Delete an LLM configuration"""
    try:
        config = LLMConfig.query.filter_by(config_id=config_id).first()
        
        if not config:
            return jsonify({'error': 'LLM config not found'}), 404
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({'message': 'LLM configuration deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete LLM config', 'details': str(e)}), 500

@admin_bp.route('/llm-configs/<config_id>/test', methods=['POST'])
@jwt_required()
@require_admin()
def test_llm_config(config_id):
    """Test an LLM configuration"""
    try:
        config = LLMConfig.query.filter_by(config_id=config_id).first()
        
        if not config:
            return jsonify({'error': 'LLM config not found'}), 404
        
        if not config.is_available():
            return jsonify({'error': 'LLM config is not available'}), 400
        
        # Import the LLM calling function
        from src.routes.analysis import call_llm_api
        
        # Test with a simple prompt
        test_prompt = "Hello! Please respond with 'Test successful' to confirm the API is working."
        
        try:
            response, tokens_used = call_llm_api(test_prompt, config)
            
            # Record the test usage
            config.record_usage(tokens_used)
            db.session.commit()
            
            return jsonify({
                'message': 'LLM configuration test successful',
                'response': response,
                'tokens_used': tokens_used
            }), 200
            
        except Exception as api_error:
            return jsonify({
                'error': 'LLM API test failed',
                'details': str(api_error)
            }), 400
        
    except Exception as e:
        return jsonify({'error': 'Failed to test LLM config', 'details': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin()
def get_users():
    """Get all users with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = User.query.order_by(User.created_at.desc())\
                    .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get users', 'details': str(e)}), 500

@admin_bp.route('/users/<user_id>/credits', methods=['PATCH'])
@jwt_required()
@require_admin()
def update_user_credits(user_id):
    """Update user credits"""
    try:
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if 'credits' not in data:
            return jsonify({'error': 'Credits amount is required'}), 400
        
        credits = data['credits']
        action = data.get('action', 'set')  # set, add, subtract
        
        if action == 'set':
            user.credits = credits
        elif action == 'add':
            user.add_credits(credits)
        elif action == 'subtract':
            user.credits = max(0, user.credits - credits)
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'User credits updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user credits', 'details': str(e)}), 500

@admin_bp.route('/system/init-defaults', methods=['POST'])
@jwt_required()
@require_admin()
def init_default_configs():
    """Initialize default LLM configurations"""
    try:
        default_configs = LLMConfig.get_default_configs()
        
        created_configs = []
        for config_data in default_configs:
            # Check if config already exists
            existing = LLMConfig.query.filter_by(
                provider=config_data['provider'],
                model_name=config_data['model_name']
            ).first()
            
            if not existing:
                config = LLMConfig(
                    provider=config_data['provider'],
                    name=config_data['name'],
                    model_name=config_data['model_name'],
                    api_endpoint=config_data['api_endpoint'],
                    cost_per_1k_tokens=config_data['cost_per_1k_tokens'],
                    is_active=False  # Require manual activation and API key
                )
                
                config.set_settings(config_data['settings'])
                
                # Set a placeholder API key
                config.set_api_key('your-api-key-here')
                
                db.session.add(config)
                created_configs.append(config_data['name'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Default configurations initialized',
            'created': created_configs
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to initialize defaults', 'details': str(e)}), 500

