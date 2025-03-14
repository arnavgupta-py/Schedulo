"""
Calendar logic for Schedulo.
Handles calendar data processing and event management.
"""

import logging
from datetime import datetime, timedelta
from database import Event, Teacher, Subject, Venue, Division, AcademicYear, Batch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_calendar_data(events):
    """
    Format events data for the calendar.
    
    Args:
        events: List of Event objects
        
    Returns:
        list: Formatted events for the calendar
    """
    formatted_data = []
    
    for event in events:
        # Skip events with missing data
        if not hasattr(event, 'subject') or not event.subject:
            logger.warning(f"Event {event.id} has no subject, skipping")
            continue
            
        event_data = {
            'id': event.id,
            'title': event.subject.name if event.subject else "Unknown Subject",
            'start': event.start_time,
            'end': event.end_time,
            'dayOfWeek': event.day_of_week,
            'teacher': event.teacher.name if event.teacher else "Unknown Teacher",
            'venue': event.venue.name if event.venue else "Unknown Venue",
            'division': event.division.name if event.division else "Unknown Division",
            'batch': event.batch.name if event.batch else None
        }
        
        formatted_data.append(event_data)
    
    return formatted_data

def validate_event_data(data):
    """
    Validate event data for updating or creating events.
    
    Args:
        data: Event data to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = ['day_of_week', 'start_time', 'end_time', 'venue_id']
    
    # Check for required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing required field: {field}"
    
    # Validate time format
    try:
        if 'start_time' in data:
            hours, minutes = map(int, data['start_time'].split(':'))
            if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
                return False, "Invalid start time format"
                
        if 'end_time' in data:
            hours, minutes = map(int, data['end_time'].split(':'))
            if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
                return False, "Invalid end time format"
    except (ValueError, AttributeError):
        return False, "Time must be in format HH:MM"
    
    # Validate that start time is before end time
    if 'start_time' in data and 'end_time' in data:
        start_parts = list(map(int, data['start_time'].split(':')))
        end_parts = list(map(int, data['end_time'].split(':')))
        
        start_minutes = start_parts[0] * 60 + start_parts[1]
        end_minutes = end_parts[0] * 60 + end_parts[1]
        
        if start_minutes >= end_minutes:
            return False, "Start time must be before end time"
    
    # Validate day of week is between 0-6
    if 'day_of_week' in data:
        try:
            day = int(data['day_of_week'])
            if day < 0 or day > 6:
                return False, "Day of week must be between 0 (Monday) and 6 (Sunday)"
        except (ValueError, TypeError):
            return False, "Day of week must be a number between 0-6"
    
    return True, ""

def check_scheduling_conflicts(event, all_events):
    """
    Check for scheduling conflicts with an event.
    
    Args:
        event: Event to check
        all_events: List of all events to check against
        
    Returns:
        dict: Information about conflicts
    """
    # Skip checking the event against itself
    if hasattr(event, 'id'):
        other_events = [e for e in all_events if e.id != event.id]
    else:
        other_events = all_events
    
    conflicts = {
        'has_conflicts': False,
        'teacher_conflicts': [],
        'venue_conflicts': [],
        'division_conflicts': [],
        'messages': []
    }
    
    # Convert event times to minutes for easier comparison
    def time_to_minutes(time_str):
        if ':' not in time_str:
            return 0
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    event_start = time_to_minutes(event.start_time)
    event_end = time_to_minutes(event.end_time)
    
    # Check each other event for conflicts
    for other_event in other_events:
        # Only check events on the same day
        if other_event.day_of_week != event.day_of_week:
            continue
        
        other_start = time_to_minutes(other_event.start_time)
        other_end = time_to_minutes(other_event.end_time)
        
        # Check if times overlap
        if event_start < other_end and event_end > other_start:
            # Teacher conflict
            if hasattr(event, 'teacher_id') and hasattr(other_event, 'teacher_id') and \
               event.teacher_id == other_event.teacher_id and event.teacher_id is not None:
                conflicts['has_conflicts'] = True
                conflicts['teacher_conflicts'].append(other_event)
                teacher_name = other_event.teacher.name if hasattr(other_event, 'teacher') and other_event.teacher else "Unknown"
                conflicts['messages'].append(
                    f"Teacher '{teacher_name}' already has class at {other_event.start_time}-{other_event.end_time}"
                )
            
            # Venue conflict
            if hasattr(event, 'venue_id') and hasattr(other_event, 'venue_id') and \
               event.venue_id == other_event.venue_id and event.venue_id is not None:
                conflicts['has_conflicts'] = True
                conflicts['venue_conflicts'].append(other_event)
                venue_name = other_event.venue.name if hasattr(other_event, 'venue') and other_event.venue else "Unknown"
                conflicts['messages'].append(
                    f"Venue '{venue_name}' already used at {other_event.start_time}-{other_event.end_time}"
                )
            
            # Division/batch conflict
            if hasattr(event, 'division_id') and hasattr(other_event, 'division_id') and \
               event.division_id == other_event.division_id and event.division_id is not None:
                # For batches, only conflict if batch_id is the same or both are None (division-wide)
                batch_conflict = False
                if (not hasattr(event, 'batch_id') or event.batch_id is None) and \
                   (not hasattr(other_event, 'batch_id') or other_event.batch_id is None):
                    batch_conflict = True
                elif hasattr(event, 'batch_id') and hasattr(other_event, 'batch_id') and \
                     event.batch_id == other_event.batch_id and event.batch_id is not None:
                    batch_conflict = True
                
                if batch_conflict:
                    conflicts['has_conflicts'] = True
                    conflicts['division_conflicts'].append(other_event)
                    division_name = other_event.division.name if hasattr(other_event, 'division') and other_event.division else "Unknown"
                    conflicts['messages'].append(
                        f"Division '{division_name}' already has class at {other_event.start_time}-{other_event.end_time}"
                    )
    
    return conflicts