"""
Tracking Configuration Routes
API endpoints for managing tracking codes (Meta Pixel, GA4, GTM, Clarity)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User
from src.models.domain import Domain
from src.models.tracking_config import TrackingConfig
import json

tracking_bp = Blueprint('tracking', __name__)

@tracking_bp.route('/platforms', methods=['GET'])
@jwt_required()
def get_platforms():
    """Get information about supported tracking platforms"""
    try:
        platforms = TrackingConfig.get_platform_info()
        return jsonify({
            'platforms': platforms,
            'message': 'Tracking platforms retrieved successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('', methods=['GET'])
@jwt_required()
def get_tracking_configs():
    """Get all tracking configurations for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        domain_id = request.args.get('domain_id', type=int)
        platform = request.args.get('platform')
        
        # Build query
        query = TrackingConfig.query.filter_by(user_id=current_user_id)
        
        if domain_id:
            query = query.filter_by(domain_id=domain_id)
        if platform:
            query = query.filter_by(platform=platform)
        
        configs = query.all()
        
        return jsonify({
            'tracking_configs': [config.to_dict() for config in configs],
            'count': len(configs)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('', methods=['POST'])
@jwt_required()
def create_tracking_config():
    """Create a new tracking configuration"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['platform', 'tracking_id', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate platform
        supported_platforms = ['meta_pixel', 'ga4', 'gtm', 'clarity']
        if data['platform'] not in supported_platforms:
            return jsonify({'error': f'Unsupported platform. Must be one of: {supported_platforms}'}), 400
        
        # Validate domain_id if provided
        domain_id = data.get('domain_id')
        if domain_id:
            domain = Domain.query.filter_by(domain_id=domain_id, user_id=current_user_id).first()
            if not domain:
                return jsonify({'error': 'Domain not found or access denied'}), 404
        
        # Check for duplicate tracking configs
        existing_config = TrackingConfig.query.filter_by(
            user_id=current_user_id,
            platform=data['platform'],
            tracking_id=data['tracking_id']
        ).first()
        
        if existing_config:
            return jsonify({'error': 'Tracking configuration already exists for this platform and ID'}), 400
        
        # Create new tracking config
        config = TrackingConfig(
            user_id=current_user_id,
            domain_id=domain_id,
            platform=data['platform'],
            tracking_id=data['tracking_id'],
            name=data['name'],
            settings=json.dumps(data.get('settings', {})) if data.get('settings') else None,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(config)
        db.session.commit()
        
        return jsonify({
            'tracking_config': config.to_dict(),
            'message': 'Tracking configuration created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/<int:config_id>', methods=['GET'])
@jwt_required()
def get_tracking_config(config_id):
    """Get a specific tracking configuration"""
    try:
        current_user_id = get_jwt_identity()
        
        config = TrackingConfig.query.filter_by(
            config_id=config_id,
            user_id=current_user_id
        ).first()
        
        if not config:
            return jsonify({'error': 'Tracking configuration not found'}), 404
        
        return jsonify({
            'tracking_config': config.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/<int:config_id>', methods=['PUT'])
@jwt_required()
def update_tracking_config(config_id):
    """Update a tracking configuration"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        config = TrackingConfig.query.filter_by(
            config_id=config_id,
            user_id=current_user_id
        ).first()
        
        if not config:
            return jsonify({'error': 'Tracking configuration not found'}), 404
        
        # Update fields
        if 'name' in data:
            config.name = data['name']
        if 'tracking_id' in data:
            config.tracking_id = data['tracking_id']
        if 'settings' in data:
            config.settings = json.dumps(data['settings']) if data['settings'] else None
        if 'is_active' in data:
            config.is_active = data['is_active']
        if 'domain_id' in data:
            domain_id = data['domain_id']
            if domain_id:
                domain = Domain.query.filter_by(domain_id=domain_id, user_id=current_user_id).first()
                if not domain:
                    return jsonify({'error': 'Domain not found or access denied'}), 404
            config.domain_id = domain_id
        
        db.session.commit()
        
        return jsonify({
            'tracking_config': config.to_dict(),
            'message': 'Tracking configuration updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/<int:config_id>', methods=['DELETE'])
@jwt_required()
def delete_tracking_config(config_id):
    """Delete a tracking configuration"""
    try:
        current_user_id = get_jwt_identity()
        
        config = TrackingConfig.query.filter_by(
            config_id=config_id,
            user_id=current_user_id
        ).first()
        
        if not config:
            return jsonify({'error': 'Tracking configuration not found'}), 404
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'message': 'Tracking configuration deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/<int:config_id>/code', methods=['GET'])
@jwt_required()
def get_tracking_code(config_id):
    """Generate tracking code for a specific configuration"""
    try:
        current_user_id = get_jwt_identity()
        
        config = TrackingConfig.query.filter_by(
            config_id=config_id,
            user_id=current_user_id
        ).first()
        
        if not config:
            return jsonify({'error': 'Tracking configuration not found'}), 404
        
        # Parse settings
        settings = None
        if config.settings:
            try:
                settings = json.loads(config.settings)
            except json.JSONDecodeError:
                settings = None
        
        # Generate tracking code
        tracking_code = TrackingConfig.generate_tracking_code(
            config.platform,
            config.tracking_id,
            settings
        )
        
        return jsonify({
            'tracking_code': tracking_code,
            'platform': config.platform,
            'tracking_id': config.tracking_id,
            'name': config.name
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/domain/<int:domain_id>/code', methods=['GET'])
@jwt_required()
def get_domain_tracking_codes(domain_id):
    """Get all tracking codes for a specific domain"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify domain ownership
        domain = Domain.query.filter_by(domain_id=domain_id, user_id=current_user_id).first()
        if not domain:
            return jsonify({'error': 'Domain not found or access denied'}), 404
        
        # Get all active tracking configs for this domain
        configs = TrackingConfig.query.filter_by(
            user_id=current_user_id,
            domain_id=domain_id,
            is_active=True
        ).all()
        
        tracking_codes = []
        for config in configs:
            settings = None
            if config.settings:
                try:
                    settings = json.loads(config.settings)
                except json.JSONDecodeError:
                    settings = None
            
            code = TrackingConfig.generate_tracking_code(
                config.platform,
                config.tracking_id,
                settings
            )
            
            tracking_codes.append({
                'config_id': config.config_id,
                'platform': config.platform,
                'name': config.name,
                'tracking_id': config.tracking_id,
                'code': code
            })
        
        # Combine all codes
        combined_code = '\n'.join([tc['code'] for tc in tracking_codes])
        
        return jsonify({
            'domain': domain.to_dict(),
            'tracking_codes': tracking_codes,
            'combined_code': combined_code,
            'count': len(tracking_codes)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/bulk-toggle', methods=['POST'])
@jwt_required()
def bulk_toggle_tracking():
    """Bulk enable/disable tracking configurations"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        config_ids = data.get('config_ids', [])
        is_active = data.get('is_active', True)
        
        if not config_ids:
            return jsonify({'error': 'No configuration IDs provided'}), 400
        
        # Update configurations
        updated_count = TrackingConfig.query.filter(
            TrackingConfig.config_id.in_(config_ids),
            TrackingConfig.user_id == current_user_id
        ).update({TrackingConfig.is_active: is_active}, synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Updated {updated_count} tracking configurations',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

