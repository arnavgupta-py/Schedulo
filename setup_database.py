# setup_database.py
import os
import sqlite3
from flask import Flask
from database import db, init_app

def setup_database():
    """Initialize the database and create all tables."""
    # Use absolute path
    DB_PATH = r"C:\Project_Directory\Schedulo\instance\schedulo.db"
    DB_DIR = os.path.dirname(DB_PATH)
    
    # Ensure instance directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    print(f"Ensuring instance directory exists: {DB_DIR}")
    print(f"Database file will be created at: {DB_PATH}")
    
    # Create empty database file first
    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"Successfully created/connected to database file")
        conn.close()
    except Exception as e:
        print(f"Error creating database file directly: {e}")
        return False
    
    # Create a temporary Flask app
    app = Flask(__name__)
    
    # Configure the app with a direct SQLite URI
    db_uri = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print(f"Using database URI: {db_uri}")
    
    # Initialize the app with the database
    init_app(app)
    
    # Create all tables
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")
    
    return True

if __name__ == "__main__":
    setup_database()