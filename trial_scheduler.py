import csv
import os
from datetime import datetime
import json
from enum import Enum
import random

class DayOfWeek(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

class AcademicYear:
    def __init__(self, symbol):
        self.symbol = symbol  # FE, SE, TE, BE
        self.divisions = []
    
    def add_division(self, division):
        self.divisions.append(division)
        division.year = self
    
    def __str__(self):
        return f"Academic Year: {self.symbol}"

class Division:
    def __init__(self, name, year=None):
        self.name = name  # Division name (e.g., "A", "B")
        self.year = year  # Reference to AcademicYear
        self.batches = []
    
    def add_batch(self, batch):
        self.batches.append(batch)
        batch.division = self
    
    def __str__(self):
        year_str = self.year.symbol if self.year else "?"
        return f"Division: {self.name} (Year: {year_str})"

class Batch:
    def __init__(self, name, division=None):
        self.name = name  # Batch name (e.g., "Batch 1")
        self.division = division  # Reference to Division
    
    def __str__(self):
        division_str = self.division.name if self.division else "?"
        return f"Batch: {self.name} (Division: {division_str})"

class Subject:
    def __init__(self, code, name, required_hours=0, subject_type="Lecture"):
        self.code = code  # Subject code
        self.name = name  # Subject name
        self.required_hours = required_hours  # Required hours per week
        self.type = subject_type  # Lecture, Lab, Tutorial
    
    def __str__(self):
        return f"Subject: {self.name} ({self.code})"

class Teacher:
    def __init__(self, id, name, workload=40):
        self.id = id  # Teacher ID
        self.name = name  # Teacher name
        self.workload = workload  # Weekly workload in hours
        self.subjects = []  # Subjects the teacher can teach
    
    def assign_subject(self, subject):
        if subject not in self.subjects:
            self.subjects.append(subject)
    
    def __str__(self):
        return f"Teacher: {self.name} (ID: {self.id})"

class Venue:
    def __init__(self, name, venue_type="Classroom", capacity=30):
        self.name = name  # Venue name (e.g., "Room 101")
        self.type = venue_type  # Classroom, Lab, etc.
        self.capacity = capacity  # Seating capacity
    
    def __str__(self):
        return f"Venue: {self.name} ({self.type}, Capacity: {self.capacity})"

class Event:
    def __init__(self, subject, teacher, venue, division, batch=None,
                 day_of_week=0, start_time="00:00", end_time="00:00",
                 is_recurring=True):
        self.subject = subject
        self.teacher = teacher
        self.venue = venue
        self.division = division
        self.batch = batch
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time
        self.is_recurring = is_recurring
    
    def __str__(self):
        batch_str = f", Batch: {self.batch.name}" if self.batch else ""
        return (f"Event: {self.subject.name} - {self.teacher.name} - "
                f"{self.venue.name} - {self.division.name}{batch_str} - "
                f"{DayOfWeek(self.day_of_week).name} - "
                f"{self.start_time} to {self.end_time}")

class Schedule:
    def __init__(self):
        # Store entities
        self.academic_years = {}
        self.divisions = {}
        self.batches = {}
        self.subjects = {}
        self.teachers = {}
        self.venues = {}
        
        # Store events (the actual timetable)
        self.events = []
    
    def add_academic_year(self, symbol):
        """Add a new academic year."""
        if symbol not in self.academic_years:
            year = AcademicYear(symbol)
            self.academic_years[symbol] = year
            return year
        return self.academic_years[symbol]
    
    def add_division(self, name, year_symbol):
        """Add a new division to an academic year."""
        key = f"{year_symbol}_{name}"
        if key not in self.divisions:
            year = self.academic_years.get(year_symbol)
            if not year:
                year = self.add_academic_year(year_symbol)
            
            division = Division(name)
            self.divisions[key] = division
            year.add_division(division)
            return division
        return self.divisions[key]
    
    def add_batch(self, name, year_symbol, division_name):
        """Add a new batch to a division."""
        key = f"{year_symbol}_{division_name}_{name}"
        if key not in self.batches:
            division_key = f"{year_symbol}_{division_name}"
            division = self.divisions.get(division_key)
            if not division:
                division = self.add_division(division_name, year_symbol)
            
            batch = Batch(name)
            self.batches[key] = batch
            division.add_batch(batch)
            return batch
        return self.batches[key]
    
    def add_subject(self, code, name, required_hours=0, subject_type="Lecture"):
        """Add a new subject."""
        if code not in self.subjects:
            subject = Subject(code, name, required_hours, subject_type)
            self.subjects[code] = subject
            return subject
        return self.subjects[code]
    
    def add_teacher(self, id, name, workload=40):
        """Add a new teacher."""
        if id not in self.teachers:
            teacher = Teacher(id, name, workload)
            self.teachers[id] = teacher
            return teacher
        return self.teachers[id]
    
    def add_venue(self, name, venue_type="Classroom", capacity=30):
        """Add a new venue."""
        if name not in self.venues:
            venue = Venue(name, venue_type, capacity)
            self.venues[name] = venue
            return venue
        return self.venues[name]
    
    def assign_teacher_to_subject(self, teacher_id, subject_code):
        """Assign a teacher to a subject."""
        teacher = self.teachers.get(teacher_id)
        subject = self.subjects.get(subject_code)
        
        if teacher and subject:
            teacher.assign_subject(subject)
            return True
        return False
    
    def add_event(self, subject_code, teacher_id, venue_name, 
                  year_symbol, division_name, batch_name=None,
                  day_of_week=0, start_time="00:00", end_time="00:00"):
        """Add a new event to the schedule."""
        subject = self.subjects.get(subject_code)
        teacher = self.teachers.get(teacher_id)
        venue = self.venues.get(venue_name)
        
        division_key = f"{year_symbol}_{division_name}"
        division = self.divisions.get(division_key)
        
        batch = None
        if batch_name:
            batch_key = f"{year_symbol}_{division_name}_{batch_name}"
            batch = self.batches.get(batch_key)
        
        if subject and teacher and venue and division:
            # Check for conflicts
            if self.check_conflicts(teacher, venue, division, batch, 
                                   day_of_week, start_time, end_time):
                print(f"Conflict detected! Event not added.")
                return None
            
            event = Event(subject, teacher, venue, division, batch,
                         day_of_week, start_time, end_time)
            self.events.append(event)
            return event
        
        print(f"Could not create event. Missing entity.")
        return None
    
    def check_conflicts(self, teacher, venue, division, batch, 
                      day_of_week, start_time, end_time):
        """Check for scheduling conflicts."""
        start_minutes = self._time_to_minutes(start_time)
        end_minutes = self._time_to_minutes(end_time)
        
        for event in self.events:
            # Skip events on different days
            if event.day_of_week != day_of_week:
                continue
            
            event_start = self._time_to_minutes(event.start_time)
            event_end = self._time_to_minutes(event.end_time)
            
            # Check if times overlap
            if start_minutes < event_end and end_minutes > event_start:
                # Teacher conflict
                if event.teacher == teacher:
                    print(f"Teacher conflict: {teacher.name} already has class at {event.start_time}-{event.end_time}")
                    return True
                
                # Venue conflict
                if event.venue == venue:
                    print(f"Venue conflict: {venue.name} already used at {event.start_time}-{event.end_time}")
                    return True
                
                # Division/batch conflict
                if event.division == division:
                    # For batches, only conflict if batch is the same or both are None (division-wide)
                    batch_conflict = False
                    if (not event.batch and not batch) or (event.batch == batch):
                        batch_conflict = True
                    
                    if batch_conflict:
                        print(f"Division conflict: {division.name} already has class at {event.start_time}-{event.end_time}")
                        return True
        
        return False
    
    def _time_to_minutes(self, time_str):
        """Convert a time string (HH:MM) to minutes."""
        if ":" not in time_str:
            return 0
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def get_events_by_division(self, year_symbol, division_name):
        """Get all events for a specific division."""
        division_key = f"{year_symbol}_{division_name}"
        division = self.divisions.get(division_key)
        
        if not division:
            return []
        
        return [e for e in self.events if e.division == division]
    
    def get_events_by_teacher(self, teacher_id):
        """Get all events for a specific teacher."""
        teacher = self.teachers.get(teacher_id)
        
        if not teacher:
            return []
        
        return [e for e in self.events if e.teacher == teacher]
    
    def get_events_by_venue(self, venue_name):
        """Get all events for a specific venue."""
        venue = self.venues.get(venue_name)
        
        if not venue:
            return []
        
        return [e for e in self.events if e.venue == venue]
    
    def get_timetable_for_division(self, year_symbol, division_name):
        """Generate a timetable for a specific division."""
        events = self.get_events_by_division(year_symbol, division_name)
        timetable = {day.name: [] for day in DayOfWeek}
        
        for event in events:
            day_name = DayOfWeek(event.day_of_week).name
            timetable[day_name].append({
                "subject": event.subject.name,
                "teacher": event.teacher.name,
                "venue": event.venue.name,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "batch": event.batch.name if event.batch else "All"
            })
        
        # Sort events by start time
        for day in timetable:
            timetable[day].sort(key=lambda x: self._time_to_minutes(x["start_time"]))
        
        return timetable
    
    def save_to_json(self, filename):
        """Save the schedule to a JSON file."""
        data = {
            "years": [{"symbol": year.symbol} for year in self.academic_years.values()],
            "divisions": [{"name": div.name, "year": div.year.symbol} 
                         for div in self.divisions.values()],
            "batches": [{"name": batch.name, "division": batch.division.name, 
                        "year": batch.division.year.symbol} 
                       for batch in self.batches.values()],
            "subjects": [{"code": subj.code, "name": subj.name, 
                         "required_hours": subj.required_hours, "type": subj.type} 
                        for subj in self.subjects.values()],
            "teachers": [{"id": t.id, "name": t.name, "workload": t.workload} 
                        for t in self.teachers.values()],
            "venues": [{"name": v.name, "type": v.type, "capacity": v.capacity} 
                      for v in self.venues.values()],
            "teacher_subjects": [{"teacher_id": t.id, "subject_codes": [s.code for s in t.subjects]} 
                               for t in self.teachers.values() if t.subjects],
            "events": [{"subject_code": e.subject.code, 
                       "teacher_id": e.teacher.id,
                       "venue_name": e.venue.name,
                       "year": e.division.year.symbol,
                       "division": e.division.name,
                       "batch": e.batch.name if e.batch else None,
                       "day_of_week": e.day_of_week,
                       "start_time": e.start_time,
                       "end_time": e.end_time} for e in self.events]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_json(self, filename):
        """Load a schedule from a JSON file."""
        if not os.path.exists(filename):
            print(f"File {filename} does not exist.")
            return False
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Clear existing data
        self.academic_years = {}
        self.divisions = {}
        self.batches = {}
        self.subjects = {}
        self.teachers = {}
        self.venues = {}
        self.events = []
        
        # Load academic years
        for year_data in data.get("years", []):
            self.add_academic_year(year_data["symbol"])
        
        # Load divisions
        for div_data in data.get("divisions", []):
            self.add_division(div_data["name"], div_data["year"])
        
        # Load batches
        for batch_data in data.get("batches", []):
            self.add_batch(batch_data["name"], batch_data["year"], batch_data["division"])
        
        # Load subjects
        for subj_data in data.get("subjects", []):
            self.add_subject(
                subj_data["code"],
                subj_data["name"],
                subj_data.get("required_hours", 0),
                subj_data.get("type", "Lecture")
            )
        
        # Load teachers
        for teacher_data in data.get("teachers", []):
            self.add_teacher(
                teacher_data["id"],
                teacher_data["name"],
                teacher_data.get("workload", 40)
            )
        
        # Load venues
        for venue_data in data.get("venues", []):
            self.add_venue(
                venue_data["name"],
                venue_data.get("type", "Classroom"),
                venue_data.get("capacity", 30)
            )
        
        # Assign teachers to subjects
        for ts_data in data.get("teacher_subjects", []):
            teacher_id = ts_data["teacher_id"]
            for subject_code in ts_data["subject_codes"]:
                self.assign_teacher_to_subject(teacher_id, subject_code)
        
        # Create events
        for event_data in data.get("events", []):
            self.add_event(
                event_data["subject_code"],
                event_data["teacher_id"],
                event_data["venue_name"],
                event_data["year"],
                event_data["division"],
                event_data.get("batch"),
                event_data["day_of_week"],
                event_data["start_time"],
                event_data["end_time"]
            )
        
        return True
    
    def export_timetable_to_csv(self, year_symbol, division_name, filename):
        """Export a division's timetable to a CSV file."""
        timetable = self.get_timetable_for_division(year_symbol, division_name)
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(["Day", "Start Time", "End Time", "Subject", "Teacher", "Venue", "Batch"])
            
            # Write rows
            for day in DayOfWeek:
                day_name = day.name
                events = timetable[day_name]
                
                for event in events:
                    writer.writerow([
                        day_name,
                        event["start_time"],
                        event["end_time"],
                        event["subject"],
                        event["teacher"],
                        event["venue"],
                        event["batch"]
                    ])
    
    def print_timetable(self, year_symbol, division_name):
        """Print a division's timetable."""
        timetable = self.get_timetable_for_division(year_symbol, division_name)
        
        print(f"\nTimetable for {year_symbol} {division_name}:")
        print("=" * 80)
        
        for day in DayOfWeek:
            day_name = day.name
            events = timetable[day_name]
            
            print(f"\n{day_name}:")
            print("-" * 80)
            
            if not events:
                print("No classes scheduled.")
                continue
            
            for event in events:
                batch_info = f" (Batch: {event['batch']})" if event['batch'] != "All" else ""
                print(f"{event['start_time']} - {event['end_time']}: "
                      f"{event['subject']} with {event['teacher']} "
                      f"at {event['venue']}{batch_info}")
    
    def generate_random_timetable(self, year_symbol, division_name, days_to_schedule=5):
        """Generate a random timetable for a division."""
        division_key = f"{year_symbol}_{division_name}"
        division = self.divisions.get(division_key)
        
        if not division:
            print(f"Division {year_symbol} {division_name} not found.")
            return False
        
        # Get all teachers and subjects
        all_teachers = list(self.teachers.values())
        if not all_teachers:
            print("No teachers available.")
            return False
        
        all_subjects = list(self.subjects.values())
        if not all_subjects:
            print("No subjects available.")
            return False
        
        all_venues = list(self.venues.values())
        if not all_venues:
            print("No venues available.")
            return False
        
        # Time slots to schedule (8:00 AM to 5:00 PM, 1-hour slots)
        time_slots = [
            ("08:00", "09:00"), ("09:00", "10:00"), ("10:00", "11:00"), 
            ("11:00", "12:00"), ("13:00", "14:00"), ("14:00", "15:00"),
            ("15:00", "16:00"), ("16:00", "17:00")
        ]
        
        # Schedule for each day
        days_to_schedule = min(days_to_schedule, 7)  # Max 7 days
        
        scheduled_count = 0
        
        for day_idx in range(days_to_schedule):
            # Schedule some random classes for this day
            classes_per_day = random.randint(3, 6)  # 3 to 6 classes per day
            
            # Shuffle time slots to randomize
            shuffled_slots = random.sample(time_slots, len(time_slots))
            
            for i in range(classes_per_day):
                if i >= len(shuffled_slots):
                    break
                
                # Pick random entities
                subject = random.choice(all_subjects)
                
                # Find teachers who can teach this subject
                eligible_teachers = [t for t in all_teachers if subject in t.subjects]
                if not eligible_teachers:
                    eligible_teachers = all_teachers  # Fallback
                
                teacher = random.choice(eligible_teachers)
                venue = random.choice(all_venues)
                
                # Decide if it's a batch session
                is_batch_session = random.choice([True, False])
                batch = None
                
                if is_batch_session and division.batches:
                    batch = random.choice(division.batches)
                
                # Add the event
                start_time, end_time = shuffled_slots[i]
                event = self.add_event(
                    subject.code, teacher.id, venue.name,
                    year_symbol, division_name, batch.name if batch else None,
                    day_idx, start_time, end_time
                )
                
                if event:
                    scheduled_count += 1
        
        print(f"Generated {scheduled_count} classes for {year_symbol} {division_name}.")
        return True

def setup_sample_data(schedule):
    """Set up sample data for demonstration."""
    # Academic years
    schedule.add_academic_year("FE")  # First Year Engineering
    schedule.add_academic_year("SE")  # Second Year Engineering
    
    # Divisions
    schedule.add_division("A", "FE")
    schedule.add_division("B", "FE")
    schedule.add_division("A", "SE")
    schedule.add_division("B", "SE")
    
    # Batches
    schedule.add_batch("1", "FE", "A")
    schedule.add_batch("2", "FE", "A")
    schedule.add_batch("1", "FE", "B")
    schedule.add_batch("2", "FE", "B")
    schedule.add_batch("1", "SE", "A")
    schedule.add_batch("2", "SE", "A")
    
    # Subjects
    schedule.add_subject("MATH101", "Mathematics I", 4)
    schedule.add_subject("PHYS101", "Physics I", 4)
    schedule.add_subject("CHEM101", "Chemistry I", 4)
    schedule.add_subject("CS101", "Introduction to Programming", 4)
    schedule.add_subject("ENG101", "English Communication", 2)
    
    schedule.add_subject("MATH201", "Mathematics II", 4)
    schedule.add_subject("PHYS201", "Physics II", 4)
    schedule.add_subject("CS201", "Data Structures", 4)
    schedule.add_subject("CS202", "Object-Oriented Programming", 4)
    schedule.add_subject("ELEC201", "Basic Electronics", 3)
    
    # Teachers
    schedule.add_teacher("T001", "Dr. Smith", 40)
    schedule.add_teacher("T002", "Prof. Johnson", 40)
    schedule.add_teacher("T003", "Dr. Williams", 40)
    schedule.add_teacher("T004", "Prof. Brown", 40)
    schedule.add_teacher("T005", "Dr. Jones", 40)
    schedule.add_teacher("T006", "Prof. Davis", 40)
    schedule.add_teacher("T007", "Dr. Miller", 40)
    schedule.add_teacher("T008", "Prof. Wilson", 40)
    
    # Assign subjects to teachers
    schedule.assign_teacher_to_subject("T001", "MATH101")
    schedule.assign_teacher_to_subject("T001", "MATH201")
    schedule.assign_teacher_to_subject("T002", "PHYS101")
    schedule.assign_teacher_to_subject("T002", "PHYS201")
    schedule.assign_teacher_to_subject("T003", "CHEM101")
    schedule.assign_teacher_to_subject("T004", "CS101")
    schedule.assign_teacher_to_subject("T004", "CS201")
    schedule.assign_teacher_to_subject("T005", "ENG101")
    schedule.assign_teacher_to_subject("T006", "CS202")
    schedule.assign_teacher_to_subject("T007", "ELEC201")
    schedule.assign_teacher_to_subject("T008", "MATH101")  # Backup for MATH101
    
    # Venues
    schedule.add_venue("Room 101", "Classroom", 60)
    schedule.add_venue("Room 102", "Classroom", 60)
    schedule.add_venue("Room 103", "Classroom", 60)
    schedule.add_venue("Room 104", "Classroom", 60)
    schedule.add_venue("Lab 1", "Computer Lab", 30)
    schedule.add_venue("Lab 2", "Computer Lab", 30)
    schedule.add_venue("Lab 3", "Physics Lab", 30)
    schedule.add_venue("Lab 4", "Chemistry Lab", 30)

def interactive_menu(schedule):
    """Interactive menu for the scheduling system."""
    while True:
        print("\n===== Academic Schedule Management System =====")
        print("1. Add/View Entities")
        print("2. Manage Timetable")
        print("3. Generate Random Timetable")
        print("4. Save/Load Schedule")
        print("5. Export Timetable")
        print("0. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == "0":
            print("Exiting...")
            break
        
        elif choice == "1":
            entity_menu(schedule)
        
        elif choice == "2":
            timetable_menu(schedule)
        
        elif choice == "3":
            year = input("Enter academic year (e.g., FE): ")
            div = input("Enter division (e.g., A): ")
            days = int(input("Enter number of days to schedule (1-7): ") or "5")
            schedule.generate_random_timetable(year, div, days)
        
        elif choice == "4":
            save_load_menu(schedule)
        
        elif choice == "5":
            year = input("Enter academic year (e.g., FE): ")
            div = input("Enter division (e.g., A): ")
            filename = input("Enter output filename (e.g., timetable.csv): ")
            schedule.export_timetable_to_csv(year, div, filename)
            print(f"Timetable exported to {filename}")
        
        else:
            print("Invalid choice. Please try again.")

def entity_menu(schedule):
    """Menu for adding and viewing entities."""
    while True:
        print("\n----- Entity Management -----")
        print("1. Add Academic Year")
        print("2. Add Division")
        print("3. Add Batch")
        print("4. Add Subject")
        print("5. Add Teacher")
        print("6. Add Venue")
        print("7. Assign Teacher to Subject")
        print("8. View All Entities")
        print("0. Back to Main Menu")
        
        choice = input("Enter your choice: ")
        
        if choice == "0":
            break
        
        elif choice == "1":
            symbol = input("Enter academic year symbol (e.g., FE, SE): ")
            schedule.add_academic_year(symbol)
            print(f"Academic year {symbol} added.")
        
        elif choice == "2":
            name = input("Enter division name (e.g., A, B): ")
            year = input("Enter academic year symbol (e.g., FE): ")
            schedule.add_division(name, year)
            print(f"Division {name} added to {year}.")
        
        elif choice == "3":
            name = input("Enter batch name (e.g., 1, 2): ")
            year = input("Enter academic year symbol (e.g., FE): ")
            div = input("Enter division name (e.g., A): ")
            schedule.add_batch(name, year, div)
            print(f"Batch {name} added to {year} {div}.")
        
        elif choice == "4":
            code = input("Enter subject code (e.g., MATH101): ")
            name = input("Enter subject name (e.g., Mathematics I): ")
            hours = int(input("Enter required hours per week (e.g., 4): ") or "0")
            type = input("Enter subject type (Lecture, Lab, etc.): ") or "Lecture"
            schedule.add_subject(code, name, hours, type)
            print(f"Subject {name} ({code}) added.")
        
        elif choice == "5":
            id = input("Enter teacher ID (e.g., T001): ")
            name = input("Enter teacher name (e.g., Dr. Smith): ")
            workload = int(input("Enter weekly workload in hours (e.g., 40): ") or "40")
            schedule.add_teacher(id, name, workload)
            print(f"Teacher {name} ({id}) added.")
        
        elif choice == "6":
            name = input("Enter venue name (e.g., Room 101): ")
            type = input("Enter venue type (Classroom, Lab, etc.): ") or "Classroom"
            capacity = int(input("Enter seating capacity (e.g., 60): ") or "30")
            schedule.add_venue(name, type, capacity)
            print(f"Venue {name} added.")
        
        elif choice == "7":
            teacher_id = input("Enter teacher ID (e.g., T001): ")
            subject_code = input("Enter subject code (e.g., MATH101): ")
            if schedule.assign_teacher_to_subject(teacher_id, subject_code):
                print(f"Teacher {teacher_id} assigned to subject {subject_code}.")
            else:
                print("Assignment failed. Check IDs.")
        
        elif choice == "8":
            print("\n--- Academic Years ---")
            for year in schedule.academic_years.values():
                print(year)
            
            print("\n--- Divisions ---")
            for div in schedule.divisions.values():
                print(div)
            
            print("\n--- Batches ---")
            for batch in schedule.batches.values():
                print(batch)
            
            print("\n--- Subjects ---")
            for subject in schedule.subjects.values():
                print(subject)
            
            print("\n--- Teachers ---")
            for teacher in schedule.teachers.values():
                print(teacher)
                print(f"  Subjects: {', '.join(s.code for s in teacher.subjects)}")
            
            print("\n--- Venues ---")
            for venue in schedule.venues.values():
                print(venue)
        
        else:
            print("Invalid choice. Please try again.")

def timetable_menu(schedule):
    """Menu for managing timetables."""
    while True:
        print("\n----- Timetable Management -----")
        print("1. Add Event")
        print("2. View Division Timetable")
        print("3. View Teacher Timetable")
        print("4. View Venue Timetable")
        print("0. Back to Main Menu")
        
        choice = input("Enter your choice: ")
        
        if choice == "0":
            break
        
        elif choice == "1":
            subject_code = input("Enter subject code: ")
            teacher_id = input("Enter teacher ID: ")
            venue_name = input("Enter venue name: ")
            year = input("Enter academic year symbol: ")
            division = input("Enter division name: ")
            
            # Optional batch
            batch = input("Enter batch name (leave empty for division-wide): ")
            if not batch:
                batch = None
            
            # Day and time
            try:
                day = int(input("Enter day of week (0=Monday, 1=Tuesday, etc.): "))
                if day < 0 or day > 6:
                    raise ValueError("Day must be between 0 and 6")
            except ValueError:
                print("Invalid day. Using Monday (0).")
                day = 0
            
            start_time = input("Enter start time (HH:MM): ")
            end_time = input("Enter end time (HH:MM): ")
            
            event = schedule.add_event(
                subject_code, teacher_id, venue_name,
                year, division, batch, day, start_time, end_time
            )
            
            if event:
                print("Event added successfully.")
        
        elif choice == "2":
            year = input("Enter academic year symbol (e.g., FE): ")
            div = input("Enter division name (e.g., A): ")
            schedule.print_timetable(year, div)
        
        elif choice == "3":
            teacher_id = input("Enter teacher ID: ")
            events = schedule.get_events_by_teacher(teacher_id)
            
            if not events:
                print(f"No events found for teacher {teacher_id}")
                continue
            
            print(f"\nTimetable for teacher {teacher_id}:")
            print("=" * 80)
            
            # Group by day
            by_day = {day.value: [] for day in DayOfWeek}
            for event in events:
                by_day[event.day_of_week].append(event)
            
            for day_idx, day_events in by_day.items():
                if not day_events:
                    continue
                
                day_name = DayOfWeek(day_idx).name
                print(f"\n{day_name}:")
                print("-" * 80)
                
                # Sort by start time
                day_events.sort(key=lambda e: schedule._time_to_minutes(e.start_time))
                
                for event in day_events:
                    print(f"{event.start_time} - {event.end_time}: "
                          f"{event.subject.name} - {event.division.year.symbol} "
                          f"{event.division.name} at {event.venue.name}")
        
        elif choice == "4":
            venue_name = input("Enter venue name: ")
            events = schedule.get_events_by_venue(venue_name)
            
            if not events:
                print(f"No events found for venue {venue_name}")
                continue
            
            print(f"\nTimetable for venue {venue_name}:")
            print("=" * 80)
            
            # Group by day
            by_day = {day.value: [] for day in DayOfWeek}
            for event in events:
                by_day[event.day_of_week].append(event)
            
            for day_idx, day_events in by_day.items():
                if not day_events:
                    continue
                
                day_name = DayOfWeek(day_idx).name
                print(f"\n{day_name}:")
                print("-" * 80)
                
                # Sort by start time
                day_events.sort(key=lambda e: schedule._time_to_minutes(e.start_time))
                
                for event in day_events:
                    print(f"{event.start_time} - {event.end_time}: "
                          f"{event.subject.name} - {event.teacher.name} - "
                          f"{event.division.year.symbol} {event.division.name}")
        
        else:
            print("Invalid choice. Please try again.")

def save_load_menu(schedule):
    """Menu for saving and loading schedules."""
    while True:
        print("\n----- Save/Load Schedule -----")
        print("1. Save Schedule to JSON")
        print("2. Load Schedule from JSON")
        print("0. Back to Main Menu")
        
        choice = input("Enter your choice: ")
        
        if choice == "0":
            break
        
        elif choice == "1":
            filename = input("Enter filename to save (e.g., schedule.json): ")
            schedule.save_to_json(filename)
            print(f"Schedule saved to {filename}")
        
        elif choice == "2":
            filename = input("Enter filename to load (e.g., schedule.json): ")
            if schedule.load_from_json(filename):
                print(f"Schedule loaded from {filename}")
            else:
                print(f"Failed to load schedule from {filename}")
        
        else:
            print("Invalid choice. Please try again.")

def main():
    """Main function."""
    print("Welcome to the Academic Scheduling System!")
    
    # Create a new schedule
    schedule = Schedule()
    
    # Ask if the user wants sample data
    use_sample = input("Do you want to use sample data? (y/n): ").lower()
    if use_sample.startswith('y'):
        setup_sample_data(schedule)
        print("Sample data loaded successfully.")
    
    # Start the interactive menu
    interactive_menu(schedule)

if __name__ == "__main__":
    main()