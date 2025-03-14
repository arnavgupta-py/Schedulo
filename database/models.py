"""
Database models for the Schedulo application.
Defines all database tables and relationships.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.types import Time
from enum import Enum

from .database import db

# Enum for days of week
class DayOfWeek(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

class User(db.Model):
    """User model for authentication and access control"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Relationships
    chat_history = db.relationship('ChatHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set the user's password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"

class AcademicYear(db.Model):
    """Academic year model representing FE, SE, TE, BE levels"""
    __tablename__ = 'academic_years'
    symbol = db.Column(db.String(2), primary_key=True)  # FE, SE, TE, BE
    
    # Relationships
    divisions = db.relationship('Division', backref='academic_year', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<AcademicYear {self.symbol}>"

class Division(db.Model):
    """Division model for organizing batches within an academic year"""
    __tablename__ = 'divisions'
    id = db.Column(db.Integer, primary_key=True)
    year_id = db.Column(db.String(2), db.ForeignKey('academic_years.symbol'), nullable=False)
    name = db.Column(db.String(20), nullable=False, index=True)
    
    # Relationships
    batches = db.relationship('Batch', backref='division', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('Event', backref='division', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('year_id', 'name', name='year_division_uc'),)
    
    def __repr__(self):
        return f"<Division {self.name} (Year: {self.year_id})>"

class Batch(db.Model):
    """Batch model for organizing students within a division"""
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    division_id = db.Column(db.Integer, db.ForeignKey('divisions.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False, index=True)
    
    # Relationships
    events = db.relationship('Event', backref='batch', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('division_id', 'name', name='division_batch_uc'),)
    
    def __repr__(self):
        return f"<Batch {self.name} (Division ID: {self.division_id})>"

class Subject(db.Model):
    """Subject model for courses taught in the institution"""
    __tablename__ = 'subjects'
    official_code = db.Column(db.String(20), primary_key=True)
    unofficial_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    required_hours_per_week = db.Column(db.Integer, default=0)
    type = db.Column(db.String(10), nullable=False, index=True)  # 'Lecture', 'Lab', or 'Extra'
    
    # Relationships
    teacher_subjects = db.relationship('TeacherSubject', backref='subject', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('Event', backref='subject', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Subject {self.official_code}: {self.name} ({self.type})>"

class Teacher(db.Model):
    """Teacher model for instructors and faculty members"""
    __tablename__ = 'teachers'
    id = db.Column(db.String(20), primary_key=True)  # ID provided by user, keeping as string for backward compatibility
    name = db.Column(db.String(100), nullable=False, index=True)
    workload = db.Column(db.Integer, default=40)  # Weekly teaching hours
    
    # Relationships
    teacher_subjects = db.relationship('TeacherSubject', backref='teacher', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('Event', backref='teacher', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Teacher {self.id}: {self.name}>"

class TeacherSubject(db.Model):
    """Association model between teachers and subjects they can teach"""
    __tablename__ = 'teacher_subjects'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(20), db.ForeignKey('teachers.id'), nullable=False)
    subject_id = db.Column(db.String(20), db.ForeignKey('subjects.official_code'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('teacher_id', 'subject_id', name='teacher_subject_uc'),)
    
    def __repr__(self):
        return f"<TeacherSubject (Teacher: {self.teacher_id}, Subject: {self.subject_id})>"

class Venue(db.Model):
    """Venue model for classrooms, labs, and other teaching spaces"""
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    type = db.Column(db.String(50), index=True)  # classroom, lab, etc.
    capacity = db.Column(db.Integer, default=30)
    
    # Relationships
    events = db.relationship('Event', backref='venue', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Venue {self.name} ({self.type})>"

class Event(db.Model):
    """Event model for scheduled classes and activities"""
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.String(20), db.ForeignKey('subjects.official_code'), nullable=True)
    teacher_id = db.Column(db.String(20), db.ForeignKey('teachers.id'), nullable=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=True)
    division_id = db.Column(db.Integer, db.ForeignKey('divisions.id'), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    day_of_week = db.Column(db.Integer, index=True)  # 0=Monday, 1=Tuesday, etc.
    start_time = db.Column(db.String(5), index=True)  # Format: "HH:MM" - kept as string for backward compatibility
    end_time = db.Column(db.String(5))  # Format: "HH:MM"
    is_recurring = db.Column(db.Boolean, default=True)
    
    def duration_minutes(self):
        """Calculate the duration of the event in minutes"""
        start_hour, start_min = map(int, self.start_time.split(':'))
        end_hour, end_min = map(int, self.end_time.split(':'))
        return (end_hour * 60 + end_min) - (start_hour * 60 + start_min)
    
    def __repr__(self):
        return f"<Event (Subject: {self.subject_id}, Day: {self.day_of_week}, Time: {self.start_time}-{self.end_time})>"

class SoftConstraint(db.Model):
    """Soft constraint model for preferences in scheduling"""
    __tablename__ = 'soft_constraints'
    id = db.Column(db.Integer, primary_key=True)
    constraint_type = db.Column(db.String(50), nullable=False, index=True)  # 'preferred_time', 'avoid_time', etc.
    entity_type = db.Column(db.String(50), index=True)  # 'teacher', 'venue', 'subject', etc.
    entity_id = db.Column(db.String(50), index=True)
    value = db.Column(db.String(100))  # JSON or simple value depending on constraint_type
    weight = db.Column(db.Integer, nullable=False, default=1)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f"<SoftConstraint {self.constraint_type} ({self.entity_type} ID: {self.entity_id})>"

class HardConstraint(db.Model):
    """Hard constraint model for requirements in scheduling"""
    __tablename__ = 'hard_constraints'
    id = db.Column(db.Integer, primary_key=True)
    constraint_type = db.Column(db.String(50), nullable=False, index=True)  # 'unavailable_time', 'required_venue', etc.
    entity_type = db.Column(db.String(50), index=True)  # 'teacher', 'venue', 'subject', etc.
    entity_id = db.Column(db.String(50), index=True)
    value = db.Column(db.String(100))  # JSON or simple value depending on constraint_type
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f"<HardConstraint {self.constraint_type} ({self.entity_type} ID: {self.entity_id})>"

class ChatHistory(db.Model):
    """Chat history model for storing conversations with the chatbot"""
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    role = db.Column(db.String(50))  # 'user' or 'assistant'
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f"<ChatHistory (User ID: {self.user_id}, Role: {self.role})>"