"""
Chatbot routes for Schedulo.
Handles AI assistant interaction and chat functionality.
"""

from flask import Blueprint, render_template, request, jsonify, session, current_app
import os
import logging
from datetime import datetime

from database import db, ChatHistory, AcademicYear
from logic.auth_logic import login_required
from logic.chatbot_logic import ScheduloAgent
from logic.scheduler_logic import check_database_completeness

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# Global agent instance
agent = None

def get_agent():
    """
    Get or initialize the chatbot agent.
    
    Returns:
        ScheduloAgent: The chatbot agent
    """
    global agent
    if agent is None:
        try:
            # Use the app's configured database URI
            db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
            
            # Get API key from environment
            api_key = os.environ.get('GROQ_API_KEY')
            if not api_key:
                logger.warning("GROQ_API_KEY not found in environment variables")
            
            # Create agent
            agent = ScheduloAgent(db_uri=db_uri, groq_api_key=api_key)
            logger.info("Schedulo Agent initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Schedulo Agent: {e}")
            return None
    return agent

@chatbot_bp.route('/')
@login_required
def index():
    """Render the chatbot interface."""
    user_id = session.get('user_id')
    
    # Fetch chat history for the user from the database
    chat_history = ChatHistory.query.filter_by(user_id=user_id).order_by(
        ChatHistory.timestamp.asc()
    ).all()
    
    # Check if database has required data for timetable generation
    missing_items = check_database_completeness()
    database_ready = len(missing_items) == 0
    
    return render_template(
        'chatbot.html', 
        chat_history=chat_history,
        database_ready=database_ready
    )

@chatbot_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Process a message from the user."""
    # Get the agent (initialize if needed)
    current_agent = get_agent()
    if not current_agent:
        return jsonify({'error': 'Chatbot service is unavailable'}), 500
    
    user_id = session.get('user_id')
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Save user message to database
    user_message = ChatHistory(
        user_id=user_id,
        role='user',
        message=message,
        timestamp=datetime.now()
    )
    db.session.add(user_message)
    db.session.commit()
    
    # Check for special "done" command
    database_complete = False
    if message.lower() == 'done':
        # Check if the database has all required data
        missing_items = check_database_completeness()
        
        if missing_items:
            # Database is incomplete
            response = "The following items are missing from the database:\n\n"
            for category, items in missing_items.items():
                response += f"**{category}:**\n"
                for item in items:
                    response += f"- {item}\n"
                response += "\n"
            response += "Please provide these missing items before generating the timetable."
        else:
            # Database is complete
            database_complete = True
            response = "Great! All required information is in the database. You can now generate the timetable."
    else:
        # Process the message with the agent
        response = current_agent.process_query(message, user_id)
    
    # Save assistant response to database
    assistant_message = ChatHistory(
        user_id=user_id,
        role='assistant',
        message=response,
        timestamp=datetime.now()
    )
    db.session.add(assistant_message)
    db.session.commit()
    
    return jsonify({
        'response': response,
        'database_complete': database_complete
    })

@chatbot_bp.route('/history')
@login_required
def get_history():
    """Get the chat history for the current user."""
    user_id = session.get('user_id')
    
    chat_history = ChatHistory.query.filter_by(user_id=user_id).order_by(
        ChatHistory.timestamp.asc()
    ).all()
    
    history = []
    for message in chat_history:
        history.append({
            'role': message.role,
            'content': message.message,
            'timestamp': message.timestamp.isoformat()
        })
    
    return jsonify({'history': history})

@chatbot_bp.route('/reset', methods=['POST'])
@login_required
def reset_conversation():
    """Reset the conversation for the current user."""
    user_id = session.get('user_id')
    
    # Reset the agent's conversation
    current_agent = get_agent()
    if current_agent:
        current_agent.reset_conversation(user_id)
    
    # Delete chat history from database
    ChatHistory.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return jsonify({'success': True})

@chatbot_bp.route('/generate-timetable', methods=['POST'])
@login_required
def generate_timetable():
    """Generate a timetable using the scheduler."""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Default to empty dict if no data
        data = data or {}
        
        # Get parameters from request
        year_id = data.get('year_id')
        time_limit = int(data.get('time_limit', 300))  # Default to 5 minutes
        
        # Log the request
        logger.info("Starting timetable generation process")
        
        # Import the solver
        from logic.scheduler_logic import solve_timetable, ORTOOLS_AVAILABLE
        logger.info(f"OR-Tools available: {ORTOOLS_AVAILABLE}")
        
        # Validate that at least some teaching data exists
        missing_items = check_database_completeness()
        if missing_items:
            missing_list = []
            for category, items in missing_items.items():
                missing_list.extend(items)
            
            return jsonify({
                "success": False,
                "message": f"Cannot generate timetable: Missing data - {', '.join(missing_list)}"
            }), 400
        
        # Start optimization
        job_id = solve_timetable(
            current_app._get_current_object(), 
            year_id=year_id, 
            time_limit_seconds=time_limit
        )
        
        if job_id:
            return jsonify({
                "success": True, 
                "message": "Timetable generation started", 
                "job_id": job_id,
                "redirect": "/calendar/"
            })
        else:
            return jsonify({
                "success": False, 
                "message": "Failed to start timetable generation. Check logs for details.",
                "redirect": "/chatbot/"
            })
    
    except Exception as e:
        logger.error(f"Error in timetable generation: {e}")
        return jsonify({
            "success": False, 
            "message": f"Error: {str(e)}",
            "redirect": "/chatbot/"
        }), 500

@chatbot_bp.route('/api/academic-years', methods=['GET'])
@login_required
def get_academic_years():
    """API endpoint to get all academic years."""
    try:
        years = AcademicYear.query.all()
        return jsonify({
            'success': True,
            'academic_years': [{'id': year.symbol, 'name': year.symbol} for year in years]
        })
    except Exception as e:
        logger.error(f"Error getting academic years: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500