from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
import stripe
import hmac
import hashlib

from src.models.user import db, User
from src.models.subscription import Subscription

billing_bp = Blueprint('billing', __name__)

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_51234567890abcdef')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_51234567890abcdef')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_1234567890abcdef')

# Pricing configuration with Stripe Price IDs
PRICING_PLANS = {
    'starter': {
        'name': 'Starter Domain',
        'price_id': os.environ.get('STRIPE_STARTER_PRICE_ID', 'price_starter_monthly'),
        'amount': 29.00,
        'credits': 10,
        'features': [
            'Full SEO + AEO Report',
            'LLMs.txt Generator',
            'Monthly Progress Tracking'
        ]
    },
    'pro': {
        'name': 'Pro Business',
        'price_id': os.environ.get('STRIPE_PRO_PRICE_ID', 'price_pro_monthly'),
        'amount': 79.00,
        'credits': 50,
        'features': [
            'Everything in Starter',
            'Advanced AEO Strategies',
            'In-depth Competitor AI Visibility',
            'Priority Support',
            'Content Semantic Insights'
        ]
    },
    'agency': {
        'name': 'Agency Scale',
        'price_id': os.environ.get('STRIPE_AGENCY_PRICE_ID', 'price_agency_monthly'),
        'amount': 199.00,
        'credits': 200,
        'features': [
            'Everything in Pro',
            'Multi-domain Management',
            'White-label Reporting',
            'API Access',
            'Dedicated Account Manager'
        ]
    }
}

def verify_webhook_signature(payload, signature):
    """Verify Stripe webhook signature"""
    try:
        stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        return True
    except ValueError:
        # Invalid payload
        return False
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return False

@billing_bp.route('/plans', methods=['GET'])
def get_pricing_plans():
    """Get available pricing plans"""
    try:
        return jsonify({
            'plans': PRICING_PLANS,
            'stripe_publishable_key': STRIPE_PUBLISHABLE_KEY
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get pricing plans', 'details': str(e)}), 500

@billing_bp.route('/subscription', methods=['GET'])
@jwt_required()
def get_subscription():
    """Get current user's subscription"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if not subscription:
            return jsonify({
                'subscription': None,
                'credits': user.credits,
                'has_subscription': False
            }), 200
        
        return jsonify({
            'subscription': subscription.to_dict(),
            'credits': user.credits,
            'has_subscription': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get subscription', 'details': str(e)}), 500

@billing_bp.route('/create-checkout-session', methods=['POST'])
@jwt_required()
def create_checkout_session():
    """Create Stripe checkout session"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        plan_name = data.get('plan')
        
        if plan_name not in PRICING_PLANS:
            return jsonify({'error': 'Invalid plan'}), 400
        
        plan = PRICING_PLANS[plan_name]
        
        # Create or get Stripe customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={
                    'user_id': user.user_id
                }
            )
            user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session
        success_url = data.get('success_url', 'https://traffictuner.com/success')
        cancel_url = data.get('cancel_url', 'https://traffictuner.com/pricing')
        
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': plan['price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'user_id': user.user_id,
                'plan_name': plan_name
            }
        )
        
        return jsonify({
            'checkout_url': session.url,
            'session_id': session.id
        }), 200
        
    except stripe.error.StripeError as e:
        return jsonify({'error': 'Stripe error', 'details': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create checkout session', 'details': str(e)}), 500

@billing_bp.route('/create-portal-session', methods=['POST'])
@jwt_required()
def create_portal_session():
    """Create Stripe customer portal session"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.stripe_customer_id:
            return jsonify({'error': 'No Stripe customer found'}), 404
        
        data = request.get_json()
        return_url = data.get('return_url', 'https://traffictuner.com/dashboard')
        
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url,
        )
        
        return jsonify({
            'portal_url': session.url
        }), 200
        
    except stripe.error.StripeError as e:
        return jsonify({'error': 'Stripe error', 'details': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create portal session', 'details': str(e)}), 500

@billing_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature')
        
        if not verify_webhook_signature(payload, signature):
            return jsonify({'error': 'Invalid signature'}), 400
        
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            handle_checkout_completed(event['data']['object'])
        elif event['type'] == 'customer.subscription.created':
            handle_subscription_created(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event['data']['object'])
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Webhook processing failed', 'details': str(e)}), 500

def handle_checkout_completed(session):
    """Handle successful checkout completion"""
    try:
        user_id = session['metadata'].get('user_id')
        plan_name = session['metadata'].get('plan_name')
        
        if not user_id or not plan_name:
            return
        
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return
        
        # Get the subscription from Stripe
        subscription_id = session['subscription']
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Create or update local subscription
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        if not subscription:
            subscription = Subscription(user_id=user.id)
            db.session.add(subscription)
        
        plan = PRICING_PLANS[plan_name]
        subscription.stripe_subscription_id = subscription_id
        subscription.stripe_customer_id = user.stripe_customer_id
        subscription.plan_name = plan_name
        subscription.status = 'active'
        subscription.monthly_credits = plan['credits']
        subscription.current_period_start = datetime.fromtimestamp(stripe_subscription['current_period_start'])
        subscription.current_period_end = datetime.fromtimestamp(stripe_subscription['current_period_end'])
        
        # Add credits to user
        user.add_credits(plan['credits'])
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error handling checkout completed: {str(e)}")

def handle_subscription_created(subscription):
    """Handle subscription creation"""
    try:
        customer_id = subscription['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if not user:
            return
        
        # Update subscription status
        local_subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription['id']
        ).first()
        
        if local_subscription:
            local_subscription.status = subscription['status']
            db.session.commit()
        
    except Exception as e:
        print(f"Error handling subscription created: {str(e)}")

def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    try:
        local_subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription['id']
        ).first()
        
        if not local_subscription:
            return
        
        local_subscription.status = subscription['status']
        local_subscription.current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
        local_subscription.current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error handling subscription updated: {str(e)}")

def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    try:
        local_subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription['id']
        ).first()
        
        if not local_subscription:
            return
        
        local_subscription.cancel()
        db.session.commit()
        
    except Exception as e:
        print(f"Error handling subscription deleted: {str(e)}")

def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    try:
        subscription_id = invoice['subscription']
        local_subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if not local_subscription:
            return
        
        # Reset monthly credits
        user = User.query.get(local_subscription.user_id)
        if user:
            plan = PRICING_PLANS.get(local_subscription.plan_name)
            if plan:
                user.add_credits(plan['credits'])
                local_subscription.credits_used = 0
                db.session.commit()
        
    except Exception as e:
        print(f"Error handling payment succeeded: {str(e)}")

def handle_payment_failed(invoice):
    """Handle failed payment"""
    try:
        subscription_id = invoice['subscription']
        local_subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if not local_subscription:
            return
        
        # Mark subscription as past due
        local_subscription.status = 'past_due'
        db.session.commit()
        
    except Exception as e:
        print(f"Error handling payment failed: {str(e)}")

@billing_bp.route('/credits/purchase', methods=['POST'])
@jwt_required()
def purchase_credits():
    """Purchase additional credits"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        credit_amount = data.get('credits', 10)
        
        # Create one-time payment for credits
        # Price per credit: $1
        amount = credit_amount * 100  # Stripe uses cents
        
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={'user_id': user.user_id}
            )
            user.stripe_customer_id = customer.id
            db.session.commit()
        
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{credit_amount} TrafficTuner Credits',
                        'description': f'Additional {credit_amount} analysis credits'
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=data.get('success_url', 'https://traffictuner.com/success'),
            cancel_url=data.get('cancel_url', 'https://traffictuner.com/pricing'),
            metadata={
                'user_id': user.user_id,
                'credits': str(credit_amount),
                'type': 'credit_purchase'
            }
        )
        
        return jsonify({
            'checkout_url': session.url,
            'session_id': session.id
        }), 200
        
    except stripe.error.StripeError as e:
        return jsonify({'error': 'Stripe error', 'details': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to purchase credits', 'details': str(e)}), 500

@billing_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage_stats():
    """Get user's usage statistics"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get subscription info
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        # Calculate usage statistics
        from src.models.analysis_report import AnalysisReport
        from src.models.domain import Domain
        
        total_analyses = AnalysisReport.query.filter_by(user_id=user.id).count()
        completed_analyses = AnalysisReport.query.filter_by(
            user_id=user.id, 
            status='completed'
        ).count()
        
        total_domains = Domain.query.filter_by(user_id=user.id).count()
        
        # Get current month usage
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_analyses = AnalysisReport.query.filter(
            AnalysisReport.user_id == user.id,
            AnalysisReport.created_at >= current_month_start
        ).count()
        
        usage_stats = {
            'credits': {
                'current': user.credits,
                'monthly_limit': subscription.monthly_credits if subscription else 0,
                'used_this_month': subscription.credits_used if subscription else 0
            },
            'analyses': {
                'total': total_analyses,
                'completed': completed_analyses,
                'this_month': monthly_analyses
            },
            'domains': {
                'total': total_domains
            },
            'subscription': subscription.to_dict() if subscription else None
        }
        
        return jsonify({'usage': usage_stats}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get usage stats', 'details': str(e)}), 500

@billing_bp.route('/cancel-subscription', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if not subscription or not subscription.stripe_subscription_id:
            return jsonify({'error': 'No active subscription found'}), 404
        
        # Cancel subscription in Stripe
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        # Update local subscription
        subscription.status = 'canceled'
        subscription.canceled_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription canceled successfully',
            'subscription': subscription.to_dict()
        }), 200
        
    except stripe.error.StripeError as e:
        return jsonify({'error': 'Stripe error', 'details': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel subscription', 'details': str(e)}), 500

