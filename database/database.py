"""
Database module for Schedulo application.
Handles database initialization and connection.
"""

import os
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_app(app=None):
    """Initialize the database with the application"""
    if app is None:
        # Create a Flask app if none is provided
        app = Flask(__name__)
        
        # Use absolute path for database
        db_path = r"C:\Project_Directory\Schedulo\instance\schedulo.db"
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        db_uri = f"sqlite:///{db_path}"
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Create all tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app
    
def create_tables(app):
    """
    Create all database tables.
    
    Args:
        app: Flask application instance
    
    Returns:
        bool: True if tables created successfully
    """
    with app.app_context():
        db.create_all()
        return True