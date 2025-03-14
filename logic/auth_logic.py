"""
Authentication logic for Schedulo.
Includes authentication, validation, and rate limiting functions.
"""

import re
import datetime
from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash

# Regular expressions for validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')

# Dictionary to track login attempts
login_attempts = {}

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def check_rate_limit(ip_address):
    """
    Check if the IP address has exceeded the rate limit for login attempts.
    
    Args:
        ip_address: IP address making the request
        
    Returns:
        bool: True if rate limit not exceeded, False otherwise
    """
    now = datetime.datetime.now()
    
    # Reset attempts older than 15 minutes
    for ip in list(login_attempts.keys()):
        if (now - login_attempts[ip]['timestamp']).total_seconds() > 900:  # 15 minutes
            del login_attempts[ip]
    
    # Check current IP
    if ip_address in login_attempts:
        attempts = login_attempts[ip_address]
        if attempts['count'] >= 5:
            # Check if lockout period is still active
            lockout_time = (now - attempts['timestamp']).total_seconds()
            if lockout_time < 900:  # 15 minutes lockout
                return False  # Rate limit exceeded
        
        attempts['count'] += 1
        attempts['timestamp'] = now
    else:
        login_attempts[ip_address] = {'count': 1, 'timestamp': now}
    
    return True  # Rate limit not exceeded

def reset_login_attempts(ip_address):
    """Reset login attempts for an IP address after successful login."""
    if ip_address in login_attempts:
        del login_attempts[ip_address]

def validate_email(email):
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(EMAIL_REGEX.match(email))

def validate_password(password):
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(PASSWORD_REGEX.match(password))

def get_login_attempt_info(ip_address):
    """
    Get information about login attempts for an IP address.
    
    Args:
        ip_address: IP address to check
        
    Returns:
        dict: Information about login attempts
    """
    now = datetime.datetime.now()
    
    if ip_address in login_attempts:
        attempts = login_attempts[ip_address]
        count = attempts['count']
        last_attempt = attempts['timestamp']
        time_since_last = (now - last_attempt).total_seconds()
        
        return {
            'count': count,
            'last_attempt': last_attempt,
            'time_since_last': time_since_last,
            'is_locked': count >= 5 and time_since_last < 900,
            'lockout_remaining': max(0, 900 - time_since_last) if count >= 5 else 0
        }
    
    return {
        'count': 0,
        'last_attempt': None,
        'time_since_last': None,
        'is_locked': False,
        'lockout_remaining': 0
    }