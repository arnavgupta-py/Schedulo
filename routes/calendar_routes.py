"""
Calendar routes for Schedulo.
Handles timetable viewing and event management.
"""

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
import logging
from sqlalchemy.orm import joinedload

from database import db, Event, Teacher, Subject, Venue, Division, AcademicYear, Batch
from logic.auth_logic import login_required
from logic.calendar_logic import format_calendar_data, validate_event_data, check_scheduling_conflicts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint (fixing the spelling from "calender" to "calendar")
calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@calendar_bp.route('/')
@login_required
def index():
    """Render the timetable view."""
    logger.info("Rendering master timetable view")
    return render_template('calendar.html')

@calendar_bp.route('/api/data')
@login_required
def get_calendar_data():
    """API endpoint to get calendar data with detailed error handling."""
    try:
        logger.info("API endpoint /api/calendar/data called")
        
        # Start with simple, hard-coded data to test the endpoint
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        basic_data = [{'day': day, 'entries': []} for day in days]
        
        try:
            # Use joinedload to fetch relations in a single query (fixes N+1 query issue)
            events = Event.query.options(
                joinedload(Event.subject),
                joinedload(Event.teacher),
                joinedload(Event.venue),
                joinedload(Event.division),
                joinedload(Event.batch)
            ).all()
            
            event_count = len(events)
            logger.info(f"Successfully fetched {event_count} events with relations")
            
            if events:
                try:
                    # Format the events data
                    formatted_data = format_calendar_data(events)
                    logger.info("Successfully formatted events data")
                    
                    return jsonify({
                        'success': True,
                        'data': formatted_data
                    })
                except Exception as format_error:
                    logger.error(f"Error formatting events: {format_error}")
                    return jsonify({
                        'success': False,
                        'data': basic_data,
                        'error': f"Error formatting events: {str(format_error)}"
                    })
            else:
                logger.info("No events found, returning empty structure")
                return jsonify({
                    'success': True,
                    'data': basic_data,
                    'message': 'No events found in the database.'
                })
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            return jsonify({
                'success': False,
                'data': basic_data,
                'error': f"Database error: {str(db_error)}"
            })
    except Exception as e:
        logger.error(f"Unhandled error in get_calendar_data: {e}")
        return jsonify({
            'success': False,
            'data': [{'day': 'Error', 'entries': []}],
            'error': f"Unhandled error: {str(e)}"
        })

@calendar_bp.route('/api/update-event', methods=['POST'])
@login_required
def update_event():
    """API endpoint to update a calendar event."""
    try:
        data = request.get_json()
        
        # Validate input data
        is_valid, error_message = validate_event_data(data)
        if not is_valid:
            return jsonify({'success': False, 'message': error_message}), 400
        
        # Required fields
        event_id = data.get('event_id')
        
        # Update the event in the database
        with db.session.begin():
            event = Event.query.get(event_id)
            if not event:
                return jsonify({'success': False, 'message': 'Event not found'}), 404
            
            # Update event fields
            if 'day_of_week' in data:
                event.day_of_week = data['day_of_week']
            if 'start_time' in data:
                event.start_time = data['start_time']
            if 'end_time' in data:
                event.end_time = data['end_time']
            if 'venue_id' in data:
                event.venue_id = data['venue_id']
            
            # Check for conflicts before committing
            conflicts = check_scheduling_conflicts(event, Event.query.all())
            if conflicts['has_conflicts'] and not data.get('force_update', False):
                return jsonify({
                    'success': False, 
                    'message': 'Scheduling conflicts detected', 
                    'conflicts': conflicts['messages'],
                    'requires_force': True
                }), 409
            
            db.session.add(event)
        
        return jsonify({'success': True, 'message': 'Event updated successfully'})
    
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@calendar_bp.route('/api/delete-event', methods=['POST'])
@login_required
def delete_event():
    """API endpoint to delete a calendar event."""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'success': False, 'message': 'Event ID is required'}), 400
        
        with db.session.begin():
            event = Event.query.get(event_id)
            if not event:
                return jsonify({'success': False, 'message': 'Event not found'}), 404
            
            db.session.delete(event)
        
        return jsonify({'success': True, 'message': 'Event deleted successfully'})
    
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@calendar_bp.route('/api/create-event', methods=['POST'])
@login_required
def create_event():
    """API endpoint to create a new calendar event."""
    try:
        data = request.get_json()
        
        # Validate input data
        is_valid, error_message = validate_event_data(data)
        if not is_valid:
            return jsonify({'success': False, 'message': error_message}), 400
        
        # Required fields
        subject_id = data.get('subject_id')
        teacher_id = data.get('teacher_id')
        venue_id = data.get('venue_id')
        division_id = data.get('division_id')
        batch_id = data.get('batch_id')
        day_of_week = data.get('day_of_week')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # Create new event
        new_event = Event(
            subject_id=subject_id,
            teacher_id=teacher_id,
            venue_id=venue_id,
            division_id=division_id,
            batch_id=batch_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_recurring=data.get('is_recurring', True)
        )
        
        # Check for conflicts before committing
        conflicts = check_scheduling_conflicts(new_event, Event.query.all())
        if conflicts['has_conflicts'] and not data.get('force_create', False):
            return jsonify({
                'success': False, 
                'message': 'Scheduling conflicts detected', 
                'conflicts': conflicts['messages'],
                'requires_force': True
            }), 409
        
        # Save to database
        with db.session.begin():
            db.session.add(new_event)
            db.session.flush()  # To get the new event ID
            event_id = new_event.id
        
        return jsonify({
            'success': True, 
            'message': 'Event created successfully',
            'event_id': event_id
        })
    
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500