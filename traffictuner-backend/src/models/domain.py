from src.models.user import db
from datetime import datetime
import uuid

class Domain(db.Model):
    __tablename__ = 'domains'
    
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Domain information
    url = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='active')  # active, analyzing, error, paused
    last_analyzed = db.Column(db.DateTime, nullable=True)
    analysis_count = db.Column(db.Integer, default=0)
    
    # SEO/AEO scores
    current_seo_score = db.Column(db.Float, nullable=True)
    current_aeo_score = db.Column(db.Float, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis_reports = db.relationship('AnalysisReport', backref='domain', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Domain {self.url}>'

    def to_dict(self):
        return {
            'id': self.id,
            'domain_id': self.domain_id,
            'user_id': self.user_id,
            'url': self.url,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
            'analysis_count': self.analysis_count,
            'current_seo_score': self.current_seo_score,
            'current_aeo_score': self.current_aeo_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def update_scores(self, seo_score, aeo_score):
        """Update the current SEO and AEO scores"""
        self.current_seo_score = seo_score
        self.current_aeo_score = aeo_score
        self.last_analyzed = datetime.utcnow()
        self.analysis_count += 1

    def set_status(self, status):
        """Update domain status"""
        self.status = status
        self.updated_at = datetime.utcnow()

    def get_latest_report(self):
        """Get the most recent analysis report"""
        return AnalysisReport.query.filter_by(domain_id=self.id).order_by(AnalysisReport.created_at.desc()).first()

    def get_score_trend(self, limit=10):
        """Get score trend over time"""
        reports = AnalysisReport.query.filter_by(domain_id=self.id)\
                    .order_by(AnalysisReport.created_at.desc())\
                    .limit(limit).all()
        
        return [{
            'date': report.created_at.isoformat(),
            'seo_score': report.seo_score,
            'aeo_score': report.aeo_score
        } for report in reversed(reports)]

