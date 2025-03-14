"""
Main application module for Schedulo.
Sets up the Flask application and registers blueprints.
"""

import os
import shutil
import logging
from flask import Flask, redirect, url_for, session, jsonify
from flask_migrate import Migrate
from flask_session import Session
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    # Create Flask application
    app = Flask(__name__)
    
    # Create and define absolute path for database
    INSTANCE_DIR = r"C:\Project_Directory\Schedulo\instance"
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
    DB_PATH = os.path.join(INSTANCE_DIR, 'schedulo.db')
    DB_URI = f"sqlite:///{DB_PATH}"
    
    # Log database path for debugging
    logger.info(f"Using database at: {DB_PATH}")
    
    # App Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Create a dedicated sessions directory
    session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_sessions')
    os.makedirs(session_dir, exist_ok=True)
    
    # Configure server-side sessions
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = session_dir
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True  # Add signature to session cookies
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Clear any existing session data at startup
    clear_sessions(session_dir)
    
    # Initialize Flask-Session
    Session(app)
    
    # Import and register blueprints
    from routes.auth_routes import auth_bp
    from routes.chatbot_routes import chatbot_bp
    from routes.calendar_routes import calendar_bp
    from routes.scheduler_routes import scheduler_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(scheduler_bp)
    
    # Import database AFTER registering blueprints
    from database import db, init_app, User
    
    # Initialize database
    init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Add API route for calendar data (shortcut)
    @app.route('/api/calendar/data')
    def get_calendar_data():
        """API endpoint to get calendar data"""
        logger.info("Root /api/calendar/data endpoint called")
        return redirect(url_for('calendar.get_calendar_data'))
    
    # Add API route for updating calendar events (shortcut)
    @app.route('/api/calendar/update-event', methods=['POST'])
    def update_calendar_event():
        """API endpoint to update calendar event"""
        logger.info("Root /api/calendar/update-event endpoint called")
        return redirect(url_for('calendar.update_event'))
    
    # Add session validation before every request
    @app.before_request
    def validate_session():
        # Check if there's a user_id in the session
        if 'user_id' in session:
            # Verify that the user actually exists in the database
            with app.app_context():
                user = User.query.get(session['user_id'])
                if not user:
                    # User doesn't exist, clear the session
                    session.clear()
    
    # Route to home page
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('chatbot.index'))
        return redirect(url_for('auth.login'))
    
    # Simple test endpoint
    @app.route('/api/test')
    def test_api():
        """Simple test endpoint to verify API is working"""
        try:
            from database import AcademicYear, Division, Batch, Event
            # Count records in different tables
            academic_years = AcademicYear.query.count()
            divisions = Division.query.count()
            batches = Batch.query.count()
            events = Event.query.count()
            
            return jsonify({
                'success': True,
                'data': {
                    'academic_years': academic_years,
                    'divisions': divisions,
                    'batches': batches,
                    'events': events,
                },
                'message': 'API is working!'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
    
    return app

def clear_sessions(session_dir):
    """Clear any existing session data."""
    if os.path.exists(session_dir):
        try:
            # Remove the directory and recreate it
            shutil.rmtree(session_dir)
            os.makedirs(session_dir, exist_ok=True)
            logger.info("Session data cleared successfully.")
        except Exception as e:
            logger.error(f"Error clearing session data: {e}")
    else:
        os.makedirs(session_dir, exist_ok=True)
        logger.info("Session directory created.")

if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs(os.path.join('static', 'css'), exist_ok=True)
    os.makedirs(os.path.join('static', 'js'), exist_ok=True)
    
    # Create and run the application
    app = create_app()
    app.run(debug=True)