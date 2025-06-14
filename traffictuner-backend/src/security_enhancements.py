"""
Security Enhancements for TrafficTuner Backend
Fixes for vulnerabilities identified in security assessment
"""

from flask import Flask, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import time
from collections import defaultdict
import threading

class SecurityEnhancements:
    def __init__(self, app):
        self.app = app
        self.failed_attempts = defaultdict(list)
        self.blocked_ips = defaultdict(datetime)
        self.lock = threading.Lock()
        
        # Configuration
        self.MAX_ATTEMPTS = 5
        self.BLOCK_DURATION = timedelta(minutes=15)
        self.ATTEMPT_WINDOW = timedelta(minutes=5)
        
    def add_security_headers(self, response):
        """Add security headers to all responses"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Remove sensitive server information
        response.headers.pop('Server', None)
        
        return response
    
    def is_ip_blocked(self, ip_address):
        """Check if IP address is currently blocked"""
        with self.lock:
            if ip_address in self.blocked_ips:
                if datetime.now() < self.blocked_ips[ip_address]:
                    return True
                else:
                    # Block expired, remove it
                    del self.blocked_ips[ip_address]
                    if ip_address in self.failed_attempts:
                        del self.failed_attempts[ip_address]
            return False
    
    def record_failed_attempt(self, ip_address):
        """Record a failed login attempt"""
        with self.lock:
            now = datetime.now()
            
            # Clean old attempts outside the window
            if ip_address in self.failed_attempts:
                self.failed_attempts[ip_address] = [
                    attempt for attempt in self.failed_attempts[ip_address]
                    if now - attempt < self.ATTEMPT_WINDOW
                ]
            
            # Add current attempt
            self.failed_attempts[ip_address].append(now)
            
            # Check if should block
            if len(self.failed_attempts[ip_address]) >= self.MAX_ATTEMPTS:
                self.blocked_ips[ip_address] = now + self.BLOCK_DURATION
                return True
            
            return False
    
    def clear_failed_attempts(self, ip_address):
        """Clear failed attempts for successful login"""
        with self.lock:
            if ip_address in self.failed_attempts:
                del self.failed_attempts[ip_address]
    
    def rate_limit_decorator(self, f):
        """Decorator for rate limiting login attempts"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            # Check if IP is blocked
            if self.is_ip_blocked(ip_address):
                return jsonify({
                    'error': 'Too many failed attempts. Please try again later.',
                    'retry_after': 900  # 15 minutes in seconds
                }), 429
            
            # Call the original function
            response = f(*args, **kwargs)
            
            # If login failed, record the attempt
            if hasattr(response, 'status_code') and response.status_code == 401:
                blocked = self.record_failed_attempt(ip_address)
                if blocked:
                    return jsonify({
                        'error': 'Too many failed attempts. Account temporarily locked.',
                        'retry_after': 900
                    }), 429
            elif hasattr(response, 'status_code') and response.status_code == 200:
                # Successful login, clear failed attempts
                self.clear_failed_attempts(ip_address)
            
            return response
        
        return decorated_function
    
    def setup_security_middleware(self):
        """Setup security middleware for the Flask app"""
        
        @self.app.after_request
        def add_security_headers_middleware(response):
            return self.add_security_headers(response)
        
        @self.app.before_request
        def security_checks():
            # Add any pre-request security checks here
            pass
        
        return self

def init_security(app):
    """Initialize security enhancements"""
    security = SecurityEnhancements(app)
    security.setup_security_middleware()
    return security

