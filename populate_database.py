# populate_data.py
import os
import random
from datetime import datetime
from flask import Flask
from database import (
    db, init_app, User, AcademicYear, Division, Batch, Subject, 
    Teacher, TeacherSubject, Venue, Event, SoftConstraint, HardConstraint
)

def create_app():
    """Create a Flask app with database configured"""
    app = Flask(__name__)
    
    # Setup database with absolute path
    DB_PATH = r"C:\Project_Directory\Schedulo\instance\schedulo.db"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    init_app(app)
    return app

def populate_test_data():
    """Populate database with test data"""
    print("Starting to populate test data...")
    
    # Clear existing data
    print("Clearing existing data...")
    db.session.query(Event).delete()
    db.session.query(TeacherSubject).delete()
    db.session.query(SoftConstraint).delete()
    db.session.query(HardConstraint).delete()
    db.session.query(Batch).delete()
    db.session.query(Division).delete()
    db.session.query(AcademicYear).delete()
    db.session.query(Teacher).delete()
    db.session.query(Subject).delete()
    db.session.query(Venue).delete()
    db.session.commit()
    
    # Create academic years
    print("Creating academic years...")
    academic_years = []
    for symbol in ["FE", "SE", "TE", "BE"]:
        year = AcademicYear(symbol=symbol)
        db.session.add(year)
        academic_years.append(year)
    db.session.commit()
    
    # Create divisions
    print("Creating divisions...")
    divisions = []
    for year in academic_years:
        for div_num in range(1, 4):  # 3 divisions per year
            division = Division(year_id=year.symbol, name=f"{year.symbol}{div_num}")
            db.session.add(division)
            divisions.append(division)
    db.session.commit()
    
    # Create batches
    print("Creating batches...")
    batches = []
    for division in divisions:
        for batch_num in range(1, 4):  # 3 batches per division
            batch = Batch(division_id=division.id, name=f"{division.name}B{batch_num}")
            db.session.add(batch)
            batches.append(batch)
    db.session.commit()
    
    # Create subjects
    print("Creating subjects...")
    subjects = []
    subject_data = [
        ("CS101", "IntroCS", "Introduction to Computer Science", 4, "Lecture"),
        ("CS102", "DSA", "Data Structures and Algorithms", 4, "Lecture"),
        ("CS103", "DBMS", "Database Management Systems", 4, "Lecture"),
        ("CS104", "OS", "Operating Systems", 4, "Lecture"),
        ("CS105", "CN", "Computer Networks", 4, "Lecture"),
        ("CS201", "AI", "Artificial Intelligence", 3, "Lecture"),
        ("CS202", "ML", "Machine Learning", 3, "Lecture"),
        ("CS203", "SE", "Software Engineering", 3, "Lecture"),
        ("CS204", "WEB", "Web Development", 3, "Lecture"),
        ("CS205", "MOB", "Mobile App Development", 3, "Lecture"),
        ("CS301", "DSLAB", "Data Structures Lab", 2, "Lab"),
        ("CS302", "DBLAB", "Database Lab", 2, "Lab"),
        ("CS303", "OSLAB", "Operating Systems Lab", 2, "Lab"),
        ("CS304", "CNLAB", "Computer Networks Lab", 2, "Lab"),
        ("CS305", "SELAB", "Software Engineering Lab", 2, "Lab")
    ]
    
    for code, ucode, name, hours, type_ in subject_data:
        subject = Subject(
            official_code=code, 
            unofficial_code=ucode, 
            name=name, 
            required_hours_per_week=hours, 
            type=type_
        )
        db.session.add(subject)
        subjects.append(subject)
    db.session.commit()
    
    # Create teachers
    print("Creating teachers...")
    teachers = []
    teacher_names = [
        "Dr. Smith", "Prof. Johnson", "Dr. Williams", "Prof. Jones",
        "Dr. Brown", "Prof. Davis", "Dr. Miller", "Prof. Wilson",
        "Dr. Moore", "Prof. Taylor", "Dr. Anderson", "Prof. Thomas",
        "Dr. Jackson", "Prof. White", "Dr. Harris", "Prof. Martin"
    ]
    
    for i, name in enumerate(teacher_names):
        teacher = Teacher(id=f"T{i+1:02d}", name=name, workload=40)
        db.session.add(teacher)
        teachers.append(teacher)
    db.session.commit()
    
    # Assign teachers to subjects
    print("Assigning teachers to subjects...")
    for teacher in teachers:
        # Assign 3-4 subjects to each teacher
        num_subjects = random.randint(3, 4)
        for subject in random.sample(subjects, num_subjects):
            teacher_subject = TeacherSubject(teacher_id=teacher.id, subject_id=subject.official_code)
            db.session.add(teacher_subject)
    db.session.commit()
    
    # Create venues
    print("Creating venues...")
    venues = []
    # Create classrooms
    for i in range(1, 11):
        venue = Venue(name=f"Classroom {i}", type="classroom")
        db.session.add(venue)
        venues.append(venue)
    
    # Create labs
    for i in range(1, 6):
        venue = Venue(name=f"Lab {i}", type="lab")
        db.session.add(venue)
        venues.append(venue)
    db.session.commit()
    
    # Create events (classes to be scheduled)
    print("Creating events...")
    for division in divisions:
        # Get year for this division to select appropriate subjects
        year_index = ["FE", "SE", "TE", "BE"].index(division.year_id)
        
        # Select subjects for this year
        year_subjects = subjects[year_index*4:(year_index+1)*4]
        if not year_subjects:
            year_subjects = subjects[:4]  # Fallback
        
        # Add lectures (for the whole division)
        for subject in year_subjects:
            # Find teachers who can teach this subject
            capable_teachers = db.session.query(TeacherSubject).filter_by(subject_id=subject.official_code).all()
            if not capable_teachers:
                continue
                
            teacher_id = random.choice(capable_teachers).teacher_id
            
            # Choose an appropriate venue
            if subject.type == "Lecture":
                available_venues = [v for v in venues if v.type == "classroom"]
            else:
                available_venues = [v for v in venues if v.type == "lab"]
            
            if not available_venues:
                available_venues = venues  # Fallback
                
            venue_id = random.choice(available_venues).id
            
            # Create event (without scheduling it yet)
            event = Event(
                subject_id=subject.official_code,
                teacher_id=teacher_id,
                venue_id=venue_id,
                division_id=division.id,
                batch_id=None,  # No batch for division-wide lectures
                day_of_week=None,  # Not scheduled yet
                start_time=None,  # Not scheduled yet
                end_time=None  # Not scheduled yet
            )
            db.session.add(event)
        
        # For practical/lab sessions, create batch-specific events
        division_batches = [b for b in batches if b.division_id == division.id]
        lab_subjects = [s for s in subjects if s.type == "Lab"]
        
        for batch in division_batches:
            for subject in lab_subjects[:2]:  # 2 labs per batch
                # Find teachers who can teach this subject
                capable_teachers = db.session.query(TeacherSubject).filter_by(subject_id=subject.official_code).all()
                if not capable_teachers:
                    continue
                    
                teacher_id = random.choice(capable_teachers).teacher_id
                
                # Choose an appropriate lab venue
                available_venues = [v for v in venues if v.type == "lab"]
                if not available_venues:
                    available_venues = venues  # Fallback
                    
                venue_id = random.choice(available_venues).id
                
                # Create event (without scheduling it yet)
                event = Event(
                    subject_id=subject.official_code,
                    teacher_id=teacher_id,
                    venue_id=venue_id,
                    division_id=division.id,
                    batch_id=batch.id,  # Batch-specific
                    day_of_week=None,  # Not scheduled yet
                    start_time=None,  # Not scheduled yet
                    end_time=None  # Not scheduled yet
                )
                db.session.add(event)
    
    db.session.commit()
    
    # Add some constraints
    print("Adding constraints...")
    
    # Hard constraints - teacher unavailability
    for teacher in teachers[:5]:  # First 5 teachers have some unavailable times
        constraint = HardConstraint(
            constraint_type="unavailable_time",
            entity_type="teacher",
            entity_id=teacher.id,
            value=f'{{"day": {random.randint(0, 4)}, "start": "14:00", "end": "17:00"}}',
            description=f"{teacher.name} is unavailable in the afternoon"
        )
        db.session.add(constraint)
    
    # Soft constraints - teacher preferences
    for teacher in teachers:
        # Morning preference
        if random.random() < 0.5:
            constraint = SoftConstraint(
                constraint_type="preferred_time",
                entity_type="teacher",
                entity_id=teacher.id,
                value=f'{{"day": "any", "start": "09:00", "end": "12:00"}}',
                weight=random.randint(1, 5),
                description=f"{teacher.name} prefers morning classes"
            )
        # Afternoon preference
        else:
            constraint = SoftConstraint(
                constraint_type="preferred_time",
                entity_type="teacher",
                entity_id=teacher.id,
                value=f'{{"day": "any", "start": "14:00", "end": "17:00"}}',
                weight=random.randint(1, 5),
                description=f"{teacher.name} prefers afternoon classes"
            )
        db.session.add(constraint)
    
    db.session.commit()
    
    # Count created records
    academic_years_count = db.session.query(AcademicYear).count()
    divisions_count = db.session.query(Division).count()
    batches_count = db.session.query(Batch).count()
    subjects_count = db.session.query(Subject).count()
    teachers_count = db.session.query(Teacher).count()
    teacher_subjects_count = db.session.query(TeacherSubject).count()
    venues_count = db.session.query(Venue).count()
    events_count = db.session.query(Event).count()
    hard_constraints_count = db.session.query(HardConstraint).count()
    soft_constraints_count = db.session.query(SoftConstraint).count()
    
    print("\nDatabase population complete!")
    print(f"Created {academic_years_count} academic years")
    print(f"Created {divisions_count} divisions")
    print(f"Created {batches_count} batches")
    print(f"Created {subjects_count} subjects")
    print(f"Created {teachers_count} teachers")
    print(f"Created {teacher_subjects_count} teacher-subject assignments")
    print(f"Created {venues_count} venues")
    print(f"Created {events_count} events (classes to be scheduled)")
    print(f"Created {hard_constraints_count} hard constraints")
    print(f"Created {soft_constraints_count} soft constraints")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        populate_test_data()