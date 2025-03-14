"""
Scheduler logic for Schedulo.
Handles timetable generation and scheduling.
"""

import os
import logging
import uuid
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Status tracking for scheduler jobs
active_jobs = {}

# Import OR-Tools if available
try:
    import helpers.ortools_bridge
    ORTOOLS_AVAILABLE = helpers.ortools_bridge.ORTOOLS_AVAILABLE
except ImportError:
    ORTOOLS_AVAILABLE = False
    logger.warning("OR-Tools bridge not available - scheduling capabilities will be limited")

def get_solver_job(job_id):
    """
    Get information about a solver job.
    
    Args:
        job_id: ID of the job
        
    Returns:
        dict: Job information
    """
    if job_id in active_jobs:
        job = active_jobs[job_id]
        elapsed_time = 0
        
        if job.get('start_time'):
            if job.get('end_time'):
                elapsed_time = (job['end_time'] - job['start_time']).total_seconds()
            else:
                elapsed_time = (datetime.now() - job['start_time']).total_seconds()
        
        stats = job.get('stats', {})
        
        return {
            'job_id': job_id,
            'status': job.get('status', 'UNKNOWN'),
            'start_time': job.get('start_time').isoformat() if job.get('start_time') else None,
            'end_time': job.get('end_time').isoformat() if job.get('end_time') else None,
            'elapsed_seconds': elapsed_time,
            'progress': job.get('progress', 0),
            'division_id': job.get('division_id'),
            'year_id': job.get('year_id'),
            'stats': stats
        }
    
    return {
        'job_id': job_id,
        'status': 'NOT_AVAILABLE'
    }

def solve_timetable(app, year_id=None, division_id=None, time_limit_seconds=60):
    """
    Solve timetable scheduling problem.
    
    Args:
        app: Flask application instance
        year_id: Academic year ID (optional)
        division_id: Division ID (optional)
        time_limit_seconds: Time limit in seconds
        
    Returns:
        str: Job ID
    """
    if not ORTOOLS_AVAILABLE:
        logger.error("OR-Tools is not available")
        return None

    try:
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Register job in active_jobs
        active_jobs[job_id] = {
            'status': 'QUEUED',
            'start_time': datetime.now(),
            'division_id': division_id,
            'year_id': year_id,
            'progress': 0
        }
        
        # Start the solver in a separate thread to avoid blocking
        import threading
        solver_thread = threading.Thread(
            target=_run_solver,
            args=(job_id, app, year_id, division_id, time_limit_seconds)
        )
        solver_thread.daemon = True
        solver_thread.start()
        
        return job_id
    except Exception as e:
        logger.error(f"Error starting solver: {e}")
        return None

def _run_solver(job_id, app, year_id, division_id, time_limit_seconds):
    """
    Run the solver in a separate thread.
    
    Args:
        job_id: Job ID
        app: Flask application instance
        year_id: Academic year ID
        division_id: Division ID
        time_limit_seconds: Time limit in seconds
    """
    if job_id not in active_jobs:
        logger.error(f"Job {job_id} not found in active jobs")
        return
    
    # Update job status
    active_jobs[job_id]['status'] = 'SOLVING'
    
    try:
        # Create application context
        with app.app_context():
            # Import here to avoid circular imports
            from database import db, AcademicYear, Division, Event, Subject, Teacher, Venue, Batch
            
            # Run the solver
            if division_id:
                # Schedule a specific division
                solution = ortools_bridge.schedule_division(
                    division_id, 
                    db.session, 
                    time_limit=time_limit_seconds
                )
            elif year_id:
                # Schedule all divisions in an academic year
                divisions = Division.query.filter_by(year_id=year_id).all()
                solutions = []
                
                for division in divisions:
                    division_solution = ortools_bridge.schedule_division(
                        division.id, 
                        db.session, 
                        time_limit=time_limit_seconds // len(divisions)
                    )
                    solutions.append(division_solution)
                
                # Combine solutions (placeholder)
                solution = solutions[0] if solutions else None
            else:
                # Schedule everything
                academic_years = AcademicYear.query.all()
                solutions = []
                
                for year in academic_years:
                    divisions = Division.query.filter_by(year_id=year.symbol).all()
                    
                    for division in divisions:
                        division_solution = ortools_bridge.schedule_division(
                            division.id, 
                            db.session, 
                            time_limit=time_limit_seconds // (len(academic_years) * len(divisions))
                        )
                        solutions.append(division_solution)
                
                # Combine solutions (placeholder)
                solution = solutions[0] if solutions else None
            
            # Update job with solution
            active_jobs[job_id]['solution'] = solution
            active_jobs[job_id]['end_time'] = datetime.now()
            
            if solution:
                active_jobs[job_id]['status'] = 'COMPLETED'
                active_jobs[job_id]['stats'] = solution.calculate_metrics() if hasattr(solution, 'calculate_metrics') else {}
            else:
                active_jobs[job_id]['status'] = 'FAILED'
    except Exception as e:
        logger.error(f"Error in solver: {e}")
        active_jobs[job_id]['status'] = 'ERROR'
        active_jobs[job_id]['error'] = str(e)
        active_jobs[job_id]['end_time'] = datetime.now()

def stop_solving(job_id):
    """
    Stop a running solver job.
    
    Args:
        job_id: ID of the job to stop
        
    Returns:
        bool: True if job was stopped, False if job not found
    """
    if job_id in active_jobs:
        job = active_jobs[job_id]
        
        if job['status'] == 'SOLVING' or job['status'] == 'QUEUED':
            job['status'] = 'STOPPED'
            job['end_time'] = datetime.now()
            return True
    
    return False

def cleanup_old_jobs(hours=24):
    """
    Clean up old jobs that have completed.
    
    Args:
        hours: Age in hours for jobs to be considered old
    """
    now = datetime.now()
    to_remove = []
    
    for job_id, job in active_jobs.items():
        if 'end_time' in job:
            age = (now - job['end_time']).total_seconds() / 3600
            if age > hours:
                to_remove.append(job_id)
    
    for job_id in to_remove:
        del active_jobs[job_id]
    
    if to_remove:
        logger.info(f"Cleaned up {len(to_remove)} old jobs")

def get_scheduling_statistics():
    """
    Get statistics about current scheduling status.
    
    Returns:
        dict: Scheduling statistics
    """
    # Initialize default statistics structure
    stats = {
        'resources': {
            'teachers': 0,
            'subjects': 0,
            'venues': 0,
            'divisions': 0,
            'academic_years': 0
        },
        'events': {
            'total': 0,
            'scheduled': 0,
            'unscheduled': 0,
            'scheduling_rate': 0
        },
        'optimization': {
            'total_jobs': len(active_jobs),
            'completed_jobs': sum(1 for job in active_jobs.values() if job.get('status') in ["COMPLETED", "PARTIAL"]),
            'success_rate': 0,
            'solver_type': "OR-Tools + Greedy Fallback" if ORTOOLS_AVAILABLE else "Greedy Algorithm"
        }
    }
    
    # Calculate success rate if there are jobs
    if stats['optimization']['total_jobs'] > 0:
        stats['optimization']['success_rate'] = (
            stats['optimization']['completed_jobs'] / stats['optimization']['total_jobs']
        )
    
    return stats

def check_database_completeness():
    """
    Check if all required data is in the database for timetable generation.
    
    Returns:
        dict: Missing items by category
    """
    try:
        # Import needed models within application context
        from database import AcademicYear, Division, Subject, Teacher, Venue
        
        missing_items = {}
        
        # Check for academic years
        academic_years = AcademicYear.query.count()
        if academic_years == 0:
            missing_items['Academic Years'] = ['No academic years defined']
        
        # Check for divisions
        divisions = Division.query.count()
        if divisions == 0:
            missing_items['Divisions'] = ['No divisions defined']
        
        # Check for subjects
        subjects = Subject.query.count()
        if subjects == 0:
            missing_items['Subjects'] = ['No subjects defined']
        
        # Check for teachers
        teachers = Teacher.query.count()
        if teachers == 0:
            missing_items['Teachers'] = ['No teachers defined']
        
        # Check for venues
        venues = Venue.query.count()
        if venues == 0:
            missing_items['Venues'] = ['No venues defined']
        
        return missing_items
    except Exception as e:
        logger.error(f"Error checking database completeness: {e}")
        return {"Error": [f"Could not check database: {str(e)}"]}