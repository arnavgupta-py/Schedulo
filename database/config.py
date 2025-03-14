"""
Configuration module for Schedulo database.
Handles environment variables and database configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration - Use absolute path for SQLite
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
instance_dir = os.path.abspath(os.path.join(basedir, 'instance'))
os.makedirs(instance_dir, exist_ok=True)

# Use os.path.join for proper path handling on Windows
DEFAULT_DB_PATH = os.path.join(instance_dir, 'schedulo.db')
# Replace forward slashes with normalized path
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DEFAULT_DB_PATH.replace(os.sep, "/")}')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')