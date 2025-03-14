"""
Authentication routes for Schedulo.
Handles login, signup, and logout functionality.
"""

from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from database import db, User, add_user, get_user_by_email
from logic.auth_logic import login_required, check_rate_limit, reset_login_attempts, validate_email, validate_password

# Create a Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.args.get('force') == 'true':
        session.clear()
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        # Basic validation
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('auth.html', active_tab='login')
        
        # Rate limiting
        if not check_rate_limit(request.remote_addr):
            flash('Too many login attempts. Please try again later.', 'danger')
            return render_template('auth.html', active_tab='login')
        
        # Authenticate user
        user = get_user_by_email(email)
        if user and user.check_password(password):
            session['user_id'] = user.id
            if remember:
                session.permanent = True
            
            # Reset login attempts on successful login
            reset_login_attempts(request.remote_addr)
            
            flash('Login successful!', 'success')
            return redirect(url_for('chatbot.index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    # GET request or failed POST
    return render_template('auth.html', active_tab='login')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration."""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate input
        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email:
            errors.append('Email is required.')
        elif not validate_email(email):
            errors.append('Please enter a valid email address.')
        if not password:
            errors.append('Password is required.')
        elif not validate_password(password):
            errors.append('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check if email already exists
        if email and User.query.filter_by(email=email).first():
            errors.append('Email is already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth.html', active_tab='signup')
        
        # Create new user
        try:
            add_user(
                email=email,
                password=password,  # Password hashing happens in add_user
                first_name=first_name,
                last_name=last_name
            )
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'danger')
    
    # GET request or failed POST
    return render_template('auth.html', active_tab='signup')

@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user_id', None)
    session.clear()
    
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))