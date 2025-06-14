from src.models.user import db
from datetime import datetime
import uuid
import json

class AnalysisReport(db.Model):
    __tablename__ = 'analysis_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Analysis metadata
    analysis_type = db.Column(db.String(50), default='full')  # full, quick, competitor
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    
    # Scores
    seo_score = db.Column(db.Float, nullable=True)
    aeo_score = db.Column(db.Float, nullable=True)
    overall_score = db.Column(db.Float, nullable=True)
    
    # Analysis results (stored as JSON)
    seo_analysis = db.Column(db.Text, nullable=True)  # JSON string
    aeo_analysis = db.Column(db.Text, nullable=True)  # JSON string
    recommendations = db.Column(db.Text, nullable=True)  # JSON string
    competitor_analysis = db.Column(db.Text, nullable=True)  # JSON string
    
    # Generated content
    llms_file_content = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    
    # Processing metadata
    processing_time = db.Column(db.Float, nullable=True)  # seconds
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<AnalysisReport {self.report_id}>'

    def to_dict(self, include_full_data=False):
        data = {
            'id': self.id,
            'report_id': self.report_id,
            'domain_id': self.domain_id,
            'user_id': self.user_id,
            'analysis_type': self.analysis_type,
            'status': self.status,
            'seo_score': self.seo_score,
            'aeo_score': self.aeo_score,
            'overall_score': self.overall_score,
            'summary': self.summary,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
        if include_full_data:
            data.update({
                'seo_analysis': self.get_seo_analysis(),
                'aeo_analysis': self.get_aeo_analysis(),
                'recommendations': self.get_recommendations(),
                'competitor_analysis': self.get_competitor_analysis(),
                'llms_file_content': self.llms_file_content,
                'error_message': self.error_message
            })
        
        return data

    def get_seo_analysis(self):
        """Parse and return SEO analysis data"""
        if self.seo_analysis:
            try:
                return json.loads(self.seo_analysis)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_seo_analysis(self, data):
        """Set SEO analysis data"""
        self.seo_analysis = json.dumps(data) if data else None

    def get_aeo_analysis(self):
        """Parse and return AEO analysis data"""
        if self.aeo_analysis:
            try:
                return json.loads(self.aeo_analysis)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_aeo_analysis(self, data):
        """Set AEO analysis data"""
        self.aeo_analysis = json.dumps(data) if data else None

    def get_recommendations(self):
        """Parse and return recommendations data"""
        if self.recommendations:
            try:
                return json.loads(self.recommendations)
            except json.JSONDecodeError:
                return []
        return []

    def set_recommendations(self, data):
        """Set recommendations data"""
        self.recommendations = json.dumps(data) if data else None

    def get_competitor_analysis(self):
        """Parse and return competitor analysis data"""
        if self.competitor_analysis:
            try:
                return json.loads(self.competitor_analysis)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_competitor_analysis(self, data):
        """Set competitor analysis data"""
        self.competitor_analysis = json.dumps(data) if data else None

    def mark_completed(self, processing_time=None):
        """Mark the analysis as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        if processing_time:
            self.processing_time = processing_time

    def mark_failed(self, error_message):
        """Mark the analysis as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def calculate_overall_score(self):
        """Calculate overall score from SEO and AEO scores"""
        if self.seo_score is not None and self.aeo_score is not None:
            self.overall_score = (self.seo_score + self.aeo_score) / 2
        elif self.seo_score is not None:
            self.overall_score = self.seo_score
        elif self.aeo_score is not None:
            self.overall_score = self.aeo_score
        else:
            self.overall_score = 0

