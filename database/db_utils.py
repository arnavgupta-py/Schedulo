"""
Database utility functions for Schedulo application.
Contains CRUD operations for all models.
"""

from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from .database import db
from .models import (
    User, AcademicYear, Division, Batch, Subject, Teacher, 
    TeacherSubject, Venue, Event, SoftConstraint, HardConstraint, ChatHistory
)

# User operations
def add_user(email, password, first_name=None, last_name=None):
    """
    Add a new user to the database.
    
    Args:
        email: User's email address
        password: User's password (will be hashed)
        first_name: User's first name (optional)
        last_name: User's last name (optional)
        
    Returns:
        User object if successful
        
    Raises:
        RuntimeError: If there's an error adding the user
    """
    try:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding user: {str(e)}")

def get_user_by_email(email):
    """
    Get a user by their email address.
    
    Args:
        email: User's email address
        
    Returns:
        User object if found, None otherwise
    """
    return User.query.filter_by(email=email).first()

def update_user(user_id, **kwargs):
    """
    Update a user's information.
    
    Args:
        user_id: ID of the user to update
        **kwargs: Attributes to update
        
    Returns:
        Updated User object if successful, None if user not found
        
    Raises:
        RuntimeError: If there's an error updating the user
    """
    try:
        user = User.query.get(user_id)
        if user:
            for key, value in kwargs.items():
                if key == 'password':
                    user.set_password(value)
                elif hasattr(user, key):
                    setattr(user, key, value)
            db.session.commit()
        return user
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error updating user: {str(e)}")

# Academic year operations
def add_academic_year(symbol):
    """
    Add a new academic year.
    
    Args:
        symbol: Academic year symbol (e.g., 'FE', 'SE')
        
    Returns:
        AcademicYear object if successful
        
    Raises:
        RuntimeError: If there's an error adding the academic year
    """
    try:
        academic_year = AcademicYear(symbol=symbol)
        db.session.add(academic_year)
        db.session.commit()
        return academic_year
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding academic year: {str(e)}")

# Division operations
def add_division(year_id, name):
    """
    Add a new division to an academic year.
    
    Args:
        year_id: ID of the academic year
        name: Name of the division
        
    Returns:
        Division object if successful
        
    Raises:
        RuntimeError: If there's an error adding the division
    """
    try:
        division = Division(year_id=year_id, name=name)
        db.session.add(division)
        db.session.commit()
        return division
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding division: {str(e)}")

def get_divisions_by_year(year_id):
    """
    Get all divisions for a specific academic year.
    
    Args:
        year_id: ID of the academic year
        
    Returns:
        List of Division objects
    """
    return Division.query.filter_by(year_id=year_id).all()

# Batch operations
def add_batch(division_id, name):
    """
    Add a new batch to a division.
    
    Args:
        division_id: ID of the division
        name: Name of the batch
        
    Returns:
        Batch object if successful
        
    Raises:
        RuntimeError: If there's an error adding the batch
    """
    try:
        batch = Batch(division_id=division_id, name=name)
        db.session.add(batch)
        db.session.commit()
        return batch
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding batch: {str(e)}")

def get_batches_by_division(division_id):
    """
    Get all batches for a specific division.
    
    Args:
        division_id: ID of the division
        
    Returns:
        List of Batch objects
    """
    return Batch.query.filter_by(division_id=division_id).all()

# Subject operations
def add_subject(official_code, unofficial_code, name, required_hours_per_week=0, type='Lecture'):
    """
    Add a new subject.
    
    Args:
        official_code: Official code of the subject
        unofficial_code: Unofficial code of the subject
        name: Name of the subject
        required_hours_per_week: Required hours per week (default: 0)
        type: Type of subject (default: 'Lecture')
        
    Returns:
        Subject object if successful
        
    Raises:
        RuntimeError: If there's an error adding the subject
    """
    try:
        subject = Subject(
            official_code=official_code,
            unofficial_code=unofficial_code,
            name=name,
            required_hours_per_week=required_hours_per_week,
            type=type
        )
        db.session.add(subject)
        db.session.commit()
        return subject
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding subject: {str(e)}")

def get_subject_by_code(official_code):
    """
    Get a subject by its official code.
    
    Args:
        official_code: Official code of the subject
        
    Returns:
        Subject object if found, None otherwise
    """
    return Subject.query.get(official_code)

# Teacher operations
def add_teacher(id, name, workload=40):
    """
    Add a new teacher.
    
    Args:
        id: ID of the teacher
        name: Name of the teacher
        workload: Weekly workload in hours (default: 40)
        
    Returns:
        Teacher object if successful
        
    Raises:
        RuntimeError: If there's an error adding the teacher
    """
    try:
        teacher = Teacher(id=id, name=name, workload=workload)
        db.session.add(teacher)
        db.session.commit()
        return teacher
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding teacher: {str(e)}")

def get_teacher_by_id(id):
    """
    Get a teacher by their ID.
    
    Args:
        id: ID of the teacher
        
    Returns:
        Teacher object if found, None otherwise
    """
    return Teacher.query.get(id)

# Teacher-Subject operations
def assign_teacher_to_subject(teacher_id, subject_id):
    """
    Assign a teacher to a subject.
    
    Args:
        teacher_id: ID of the teacher
        subject_id: ID of the subject
        
    Returns:
        TeacherSubject object if successful
        
    Raises:
        RuntimeError: If there's an error assigning the teacher
    """
    try:
        # Check if the assignment already exists
        existing = TeacherSubject.query.filter_by(
            teacher_id=teacher_id, subject_id=subject_id
        ).first()
        
        if not existing:
            teacher_subject = TeacherSubject(teacher_id=teacher_id, subject_id=subject_id)
            db.session.add(teacher_subject)
            db.session.commit()
            return teacher_subject
        return existing
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error assigning teacher to subject: {str(e)}")

def get_subjects_by_teacher(teacher_id):
    """
    Get all subjects taught by a specific teacher.
    
    Args:
        teacher_id: ID of the teacher
        
    Returns:
        List of Subject objects
    """
    teacher_subjects = TeacherSubject.query.filter_by(teacher_id=teacher_id).all()
    return [ts.subject for ts in teacher_subjects]

def get_teachers_by_subject(subject_id):
    """
    Get all teachers who can teach a specific subject.
    
    Args:
        subject_id: ID of the subject
        
    Returns:
        List of Teacher objects
    """
    teacher_subjects = TeacherSubject.query.filter_by(subject_id=subject_id).all()
    return [ts.teacher for ts in teacher_subjects]

# Venue operations
def add_venue(name, type=None, capacity=30):
    """
    Add a new venue.
    
    Args:
        name: Name of the venue
        type: Type of venue (default: None)
        capacity: Capacity of the venue (default: 30)
        
    Returns:
        Venue object if successful
        
    Raises:
        RuntimeError: If there's an error adding the venue
    """
    try:
        venue = Venue(name=name, type=type, capacity=capacity)
        db.session.add(venue)
        db.session.commit()
        return venue
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding venue: {str(e)}")

def get_venue_by_name(name):
    """
    Get a venue by its name.
    
    Args:
        name: Name of the venue
        
    Returns:
        Venue object if found, None otherwise
    """
    return Venue.query.filter_by(name=name).first()

# Event operations
def add_event(subject_id, teacher_id, venue_id, division_id, batch_id=None, 
              day_of_week=0, start_time="00:00", end_time="00:00", is_recurring=True):
    """
    Add a new event to the schedule.
    
    Args:
        subject_id: ID of the subject
        teacher_id: ID of the teacher
        venue_id: ID of the venue
        division_id: ID of the division
        batch_id: ID of the batch (default: None)
        day_of_week: Day of the week (0=Monday, 1=Tuesday, etc.) (default: 0)
        start_time: Start time (format: "HH:MM") (default: "00:00")
        end_time: End time (format: "HH:MM") (default: "00:00")
        is_recurring: Whether the event is recurring (default: True)
        
    Returns:
        Event object if successful
        
    Raises:
        RuntimeError: If there's an error adding the event
    """
    try:
        event = Event(
            subject_id=subject_id,
            teacher_id=teacher_id,
            venue_id=venue_id,
            division_id=division_id,
            batch_id=batch_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_recurring=is_recurring
        )
        db.session.add(event)
        db.session.commit()
        return event
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding event: {str(e)}")

def update_event(event_id, **kwargs):
    """
    Update an event's information.
    
    Args:
        event_id: ID of the event to update
        **kwargs: Attributes to update
        
    Returns:
        Updated Event object if successful, None if event not found
        
    Raises:
        RuntimeError: If there's an error updating the event
    """
    try:
        event = Event.query.get(event_id)
        if event:
            for key, value in kwargs.items():
                if hasattr(event, key):
                    setattr(event, key, value)
            db.session.commit()
        return event
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error updating event: {str(e)}")

def delete_event(event_id):
    """
    Delete an event from the schedule.
    
    Args:
        event_id: ID of the event to delete
        
    Returns:
        Deleted Event object if successful, None if event not found
        
    Raises:
        RuntimeError: If there's an error deleting the event
    """
    try:
        event = Event.query.get(event_id)
        if event:
            db.session.delete(event)
            db.session.commit()
        return event
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error deleting event: {str(e)}")

def get_events_by_division(division_id):
    """Get all events for a specific division."""
    return Event.query.filter_by(division_id=division_id).all()

def get_events_by_teacher(teacher_id):
    """Get all events for a specific teacher."""
    return Event.query.filter_by(teacher_id=teacher_id).all()

def get_events_by_venue(venue_id):
    """Get all events for a specific venue."""
    return Event.query.filter_by(venue_id=venue_id).all()

# Constraint operations
def add_soft_constraint(constraint_type, entity_type, entity_id, value, weight=1, description=None):
    """
    Add a new soft constraint.
    
    Args:
        constraint_type: Type of constraint (e.g., 'preferred_time')
        entity_type: Type of entity (e.g., 'teacher')
        entity_id: ID of the entity
        value: Constraint value
        weight: Constraint weight (default: 1)
        description: Constraint description (default: None)
        
    Returns:
        SoftConstraint object if successful
        
    Raises:
        RuntimeError: If there's an error adding the constraint
    """
    try:
        constraint = SoftConstraint(
            constraint_type=constraint_type,
            entity_type=entity_type,
            entity_id=entity_id,
            value=value,
            weight=weight,
            description=description
        )
        db.session.add(constraint)
        db.session.commit()
        return constraint
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding soft constraint: {str(e)}")

def add_hard_constraint(constraint_type, entity_type, entity_id, value, description=None):
    """
    Add a new hard constraint.
    
    Args:
        constraint_type: Type of constraint (e.g., 'unavailable_time')
        entity_type: Type of entity (e.g., 'teacher')
        entity_id: ID of the entity
        value: Constraint value
        description: Constraint description (default: None)
        
    Returns:
        HardConstraint object if successful
        
    Raises:
        RuntimeError: If there's an error adding the constraint
    """
    try:
        constraint = HardConstraint(
            constraint_type=constraint_type,
            entity_type=entity_type,
            entity_id=entity_id,
            value=value,
            description=description
        )
        db.session.add(constraint)
        db.session.commit()
        return constraint
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding hard constraint: {str(e)}")

def get_constraints_for_scheduling():
    """
    Get all constraints for use in the scheduling algorithm.
    
    Returns:
        Dictionary with 'hard' and 'soft' constraints
    """
    hard_constraints = HardConstraint.query.all()
    soft_constraints = SoftConstraint.query.all()
    return {
        'hard': hard_constraints,
        'soft': soft_constraints
    }

# Chat history operations
def add_chat_message(user_id, role, message):
    """
    Add a new chat message to the history.
    
    Args:
        user_id: ID of the user
        role: Role ('user' or 'assistant')
        message: Message content
        
    Returns:
        ChatHistory object if successful
        
    Raises:
        RuntimeError: If there's an error adding the message
    """
    try:
        chat_entry = ChatHistory(
            user_id=user_id,
            role=role,
            message=message,
            timestamp=datetime.now()
        )
        db.session.add(chat_entry)
        db.session.commit()
        return chat_entry
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError(f"Error adding chat message: {str(e)}")

def get_chat_history_by_user(user_id, limit=50):
    """
    Get recent chat history for a specific user.
    
    Args:
        user_id: ID of the user
        limit: Maximum number of messages to retrieve (default: 50)
        
    Returns:
        List of ChatHistory objects
    """
    return ChatHistory.query.filter_by(user_id=user_id).order_by(
        ChatHistory.timestamp.desc()
    ).limit(limit).all()