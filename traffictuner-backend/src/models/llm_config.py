from src.models.user import db
from datetime import datetime
import uuid
import json
from cryptography.fernet import Fernet
import os

class LLMConfig(db.Model):
    __tablename__ = 'llm_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    config_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Provider information
    provider = db.Column(db.String(50), nullable=False)  # openai, anthropic, google, custom
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # API configuration
    api_key_encrypted = db.Column(db.Text, nullable=False)
    api_endpoint = db.Column(db.String(255), nullable=True)
    model_name = db.Column(db.String(100), nullable=False)
    
    # Configuration settings (stored as JSON)
    settings = db.Column(db.Text, nullable=True)  # JSON string for additional settings
    
    # Usage and limits
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=1)  # Higher number = higher priority
    rate_limit_per_minute = db.Column(db.Integer, default=60)
    cost_per_1k_tokens = db.Column(db.Float, default=0.0)
    
    # Usage tracking
    total_requests = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    last_used = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<LLMConfig {self.provider}:{self.model_name}>'

    @property
    def encryption_key(self):
        """Get or create encryption key for API keys"""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # Generate a new key if not exists (for development)
            key = Fernet.generate_key().decode()
            os.environ['ENCRYPTION_KEY'] = key
        return key.encode()

    def set_api_key(self, api_key):
        """Encrypt and store API key"""
        f = Fernet(self.encryption_key)
        self.api_key_encrypted = f.encrypt(api_key.encode()).decode()

    def get_api_key(self):
        """Decrypt and return API key"""
        if not self.api_key_encrypted:
            return None
        try:
            f = Fernet(self.encryption_key)
            return f.decrypt(self.api_key_encrypted.encode()).decode()
        except Exception:
            return None

    def get_settings(self):
        """Parse and return settings data"""
        if self.settings:
            try:
                return json.loads(self.settings)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_settings(self, data):
        """Set settings data"""
        self.settings = json.dumps(data) if data else None

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'config_id': self.config_id,
            'provider': self.provider,
            'name': self.name,
            'description': self.description,
            'model_name': self.model_name,
            'api_endpoint': self.api_endpoint,
            'settings': self.get_settings(),
            'is_active': self.is_active,
            'priority': self.priority,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'cost_per_1k_tokens': self.cost_per_1k_tokens,
            'total_requests': self.total_requests,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data['api_key'] = self.get_api_key()
        else:
            # Show masked API key
            api_key = self.get_api_key()
            if api_key:
                data['api_key_masked'] = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            else:
                data['api_key_masked'] = None
        
        return data

    def record_usage(self, tokens_used, cost=None):
        """Record API usage"""
        self.total_requests += 1
        self.total_tokens += tokens_used
        if cost:
            self.total_cost += cost
        else:
            # Calculate cost based on rate
            self.total_cost += (tokens_used / 1000) * self.cost_per_1k_tokens
        self.last_used = datetime.utcnow()

    def is_available(self):
        """Check if LLM config is available for use"""
        return self.is_active and self.get_api_key() is not None

    @staticmethod
    def get_active_config(provider=None):
        """Get the highest priority active config"""
        query = LLMConfig.query.filter_by(is_active=True)
        if provider:
            query = query.filter_by(provider=provider)
        return query.order_by(LLMConfig.priority.desc()).first()

    @staticmethod
    def get_default_configs():
        """Get default LLM configurations"""
        return [
            {
                'provider': 'openai',
                'name': 'OpenAI GPT-4',
                'model_name': 'gpt-4',
                'api_endpoint': 'https://api.openai.com/v1',
                'cost_per_1k_tokens': 0.03,
                'settings': {
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
            },
            {
                'provider': 'anthropic',
                'name': 'Claude 3 Sonnet',
                'model_name': 'claude-3-sonnet-20240229',
                'api_endpoint': 'https://api.anthropic.com/v1',
                'cost_per_1k_tokens': 0.015,
                'settings': {
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
            }
        ]

