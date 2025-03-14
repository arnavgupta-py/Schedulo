"""
Initialization module for Schedulo database package.
"""

from .database import db, init_app, create_tables
from .models import (
    User, AcademicYear, Division, Batch, Subject, Teacher, 
    TeacherSubject, Venue, Event, SoftConstraint, HardConstraint, ChatHistory
)
from .db_utils import (
    add_user, get_user_by_email, update_user,
    add_academic_year,
    add_division, get_divisions_by_year,
    add_batch, get_batches_by_division,
    add_subject, get_subject_by_code,
    add_teacher, get_teacher_by_id,
    assign_teacher_to_subject, get_subjects_by_teacher, get_teachers_by_subject,
    add_venue, get_venue_by_name,
    add_event, update_event, delete_event, get_events_by_division, get_events_by_teacher, get_events_by_venue,
    add_soft_constraint, add_hard_constraint, get_constraints_for_scheduling,
    add_chat_message, get_chat_history_by_user
)

# Aliases for backward compatibility
from .models import DayOfWeek