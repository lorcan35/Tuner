from src.models.user import db
from datetime import datetime
import uuid

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Stripe integration
    stripe_subscription_id = db.Column(db.String(100), unique=True, nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    stripe_price_id = db.Column(db.String(100), nullable=True)
    
    # Subscription details
    plan_name = db.Column(db.String(50), nullable=False)  # starter, pro, agency
    status = db.Column(db.String(20), default='active')  # active, canceled, past_due, unpaid
    
    # Billing cycle
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    
    # Credits and limits
    monthly_credits = db.Column(db.Integer, default=0)
    credits_used = db.Column(db.Integer, default=0)
    credits_remaining = db.Column(db.Integer, default=0)
    
    # Pricing
    amount = db.Column(db.Float, nullable=True)  # Monthly amount in dollars
    currency = db.Column(db.String(3), default='USD')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    canceled_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Subscription {self.plan_name} for User {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'user_id': self.user_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'plan_name': self.plan_name,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'monthly_credits': self.monthly_credits,
            'credits_used': self.credits_used,
            'credits_remaining': self.credits_remaining,
            'amount': self.amount,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None
        }

    def is_active(self):
        """Check if subscription is active"""
        return self.status == 'active' and (
            self.current_period_end is None or 
            self.current_period_end > datetime.utcnow()
        )

    def has_credits(self):
        """Check if subscription has remaining credits"""
        return self.credits_remaining > 0

    def use_credit(self):
        """Use one credit from the subscription"""
        if self.credits_remaining > 0:
            self.credits_remaining -= 1
            self.credits_used += 1
            return True
        return False

    def reset_monthly_credits(self):
        """Reset credits for new billing period"""
        self.credits_used = 0
        self.credits_remaining = self.monthly_credits

    def cancel(self):
        """Cancel the subscription"""
        self.status = 'canceled'
        self.canceled_at = datetime.utcnow()

    @staticmethod
    def get_plan_details(plan_name):
        """Get plan details by name"""
        plans = {
            'starter': {
                'name': 'Starter Domain',
                'price': 29,
                'credits': 10,
                'features': ['Full SEO + AEO Report', 'LLMs.txt Generator', 'Monthly Progress Tracking']
            },
            'pro': {
                'name': 'Pro Business',
                'price': 79,
                'credits': 50,
                'features': ['Everything in Starter', 'Advanced AEO Strategies', 'In-depth Competitor AI Visibility', 'Priority Support', 'Content Semantic Insights']
            },
            'agency': {
                'name': 'Agency Scale',
                'price': 199,
                'credits': 200,
                'features': ['Everything in Pro', 'Multi-domain Management', 'White-label Reporting', 'API Access', 'Dedicated Account Manager']
            }
        }
        return plans.get(plan_name, {})

