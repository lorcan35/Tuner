from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import validators
from urllib.parse import urlparse

from src.models.user import db, User
from src.models.domain import Domain
from src.models.analysis_report import AnalysisReport

domains_bp = Blueprint('domains', __name__)

def validate_url(url):
    """Validate and normalize URL"""
    if not url:
        return None, "URL is required"
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Validate URL format
    if not validators.url(url):
        return None, "Invalid URL format"
    
    # Parse and normalize
    parsed = urlparse(url)
    normalized_url = f"{parsed.scheme}://{parsed.netloc}"
    
    return normalized_url, None

@domains_bp.route('', methods=['GET'])
@jwt_required()
def get_domains():
    """Get all domains for the current user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        domains = Domain.query.filter_by(user_id=user.id).order_by(Domain.created_at.desc()).all()
        
        domains_data = []
        for domain in domains:
            domain_data = domain.to_dict()
            # Add latest report info
            latest_report = domain.get_latest_report()
            if latest_report:
                domain_data['latest_report'] = {
                    'report_id': latest_report.report_id,
                    'status': latest_report.status,
                    'created_at': latest_report.created_at.isoformat()
                }
            domains_data.append(domain_data)
        
        return jsonify({
            'domains': domains_data,
            'total': len(domains_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get domains', 'details': str(e)}), 500

@domains_bp.route('', methods=['POST'])
@jwt_required()
def add_domain():
    """Add a new domain for analysis"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate URL
        url, error = validate_url(data.get('url'))
        if error:
            return jsonify({'error': error}), 400
        
        # Check if domain already exists for this user
        existing_domain = Domain.query.filter_by(user_id=user.id, url=url).first()
        if existing_domain:
            return jsonify({'error': 'Domain already exists'}), 409
        
        # Create new domain
        domain = Domain(
            user_id=user.id,
            url=url,
            name=data.get('name', urlparse(url).netloc),
            description=data.get('description'),
            status='active'
        )
        
        db.session.add(domain)
        db.session.commit()
        
        return jsonify({
            'message': 'Domain added successfully',
            'domain': domain.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add domain', 'details': str(e)}), 500

@domains_bp.route('/<domain_id>', methods=['GET'])
@jwt_required()
def get_domain(domain_id):
    """Get a specific domain"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        domain = Domain.query.filter_by(domain_id=domain_id, user_id=user.id).first()
        
        if not domain:
            return jsonify({'error': 'Domain not found'}), 404
        
        domain_data = domain.to_dict()
        
        # Add reports
        reports = AnalysisReport.query.filter_by(domain_id=domain.id)\
                    .order_by(AnalysisReport.created_at.desc()).all()
        domain_data['reports'] = [report.to_dict() for report in reports]
        
        # Add score trend
        domain_data['score_trend'] = domain.get_score_trend()
        
        return jsonify({'domain': domain_data}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get domain', 'details': str(e)}), 500

@domains_bp.route('/<domain_id>', methods=['PATCH'])
@jwt_required()
def update_domain(domain_id):
    """Update domain information"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        domain = Domain.query.filter_by(domain_id=domain_id, user_id=user.id).first()
        
        if not domain:
            return jsonify({'error': 'Domain not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            domain.name = data['name']
        
        if 'description' in data:
            domain.description = data['description']
        
        if 'status' in data and data['status'] in ['active', 'paused']:
            domain.status = data['status']
        
        domain.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Domain updated successfully',
            'domain': domain.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update domain', 'details': str(e)}), 500

@domains_bp.route('/<domain_id>', methods=['DELETE'])
@jwt_required()
def delete_domain(domain_id):
    """Delete a domain"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        domain = Domain.query.filter_by(domain_id=domain_id, user_id=user.id).first()
        
        if not domain:
            return jsonify({'error': 'Domain not found'}), 404
        
        db.session.delete(domain)
        db.session.commit()
        
        return jsonify({'message': 'Domain deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete domain', 'details': str(e)}), 500

@domains_bp.route('/<domain_id>/reports', methods=['GET'])
@jwt_required()
def get_domain_reports(domain_id):
    """Get all reports for a domain"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        domain = Domain.query.filter_by(domain_id=domain_id, user_id=user.id).first()
        
        if not domain:
            return jsonify({'error': 'Domain not found'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        reports = AnalysisReport.query.filter_by(domain_id=domain.id)\
                    .order_by(AnalysisReport.created_at.desc())\
                    .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'reports': [report.to_dict() for report in reports.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': reports.total,
                'pages': reports.pages,
                'has_next': reports.has_next,
                'has_prev': reports.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reports', 'details': str(e)}), 500

@domains_bp.route('/<domain_id>/analyze', methods=['POST'])
@jwt_required()
def analyze_domain(domain_id):
    """Trigger analysis for a domain"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user has credits
        if not user.can_analyze():
            return jsonify({'error': 'Insufficient credits'}), 402
        
        domain = Domain.query.filter_by(domain_id=domain_id, user_id=user.id).first()
        
        if not domain:
            return jsonify({'error': 'Domain not found'}), 404
        
        # Check if domain is already being analyzed
        pending_report = AnalysisReport.query.filter_by(
            domain_id=domain.id, 
            status='pending'
        ).first()
        
        if pending_report:
            return jsonify({'error': 'Analysis already in progress'}), 409
        
        # Create new analysis report
        analysis_type = request.get_json().get('analysis_type', 'full')
        
        report = AnalysisReport(
            domain_id=domain.id,
            user_id=user.id,
            analysis_type=analysis_type,
            status='pending'
        )
        
        db.session.add(report)
        
        # Deduct credit
        user.deduct_credit()
        
        # Update domain status
        domain.set_status('analyzing')
        
        db.session.commit()
        
        # Queue analysis job for background processing
        from src.services.analysis_worker import get_worker
        worker = get_worker()
        if worker:
            worker.queue_analysis(report.report_id)
        
        return jsonify({
            'message': 'Analysis started successfully',
            'report': report.to_dict(),
            'credits_remaining': user.credits
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to start analysis', 'details': str(e)}), 500

