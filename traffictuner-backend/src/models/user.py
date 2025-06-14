from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(20), nullable=False, default='USER')  # USER, AGENCY, SUPER_ADMIN
    
    # OAuth providers
    oauth_google_id = db.Column(db.String(100), nullable=True)
    oauth_github_id = db.Column(db.String(100), nullable=True)
    
    # Security
    two_factor_secret = db.Column(db.String(32), nullable=True)
    
    # Stripe integration
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    
    # User experience
    is_new_user = db.Column(db.Boolean, default=True)
    credits = db.Column(db.Integer, default=3)  # Free trial credits
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    domains = db.relationship('Domain', backref='owner', lazy=True, cascade='all, delete-orphan')
    analysis_reports = db.relationship('AnalysisReport', backref='user', lazy=True)
    subscription = db.relationship('Subscription', backref='user', uselist=False, lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'role': self.role,
            'is_new_user': self.is_new_user,
            'credits': self.credits,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data.update({
                'stripe_customer_id': self.stripe_customer_id,
                'stripe_subscription_id': self.stripe_subscription_id,
                'oauth_google_id': self.oauth_google_id,
                'oauth_github_id': self.oauth_github_id
            })
        
        return data

    def has_role(self, role):
        """Check if user has a specific role"""
        return self.role == role

    def is_admin(self):
        """Check if user is admin"""
        return self.role in ['SUPER_ADMIN', 'ADMIN']

    def can_analyze(self):
        """Check if user has credits to perform analysis"""
        return self.credits > 0

    def deduct_credit(self):
        """Deduct one credit from user"""
        if self.credits > 0:
            self.credits -= 1
            return True
        return False

    def add_credits(self, amount):
        """Add credits to user account"""
        self.credits += amount

