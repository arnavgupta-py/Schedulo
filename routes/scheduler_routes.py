"""
Scheduler routes for Schedulo.
Handles timetable optimization and scheduling.
"""

from flask import Blueprint, request, jsonify, render_template, current_app, url_for, redirect, session, flash
import logging
import time
import threading

from database import db, Division, AcademicYear, HardConstraint, SoftConstraint
from logic.auth_logic import login_required
from logic.scheduler_logic import (
    solve_timetable, get_solver_job, stop_solving, 
    get_scheduling_statistics, ORTOOLS_AVAILABLE, cleanup_old_jobs
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/scheduler')

# Scheduling status polling interval in milliseconds
POLLING_INTERVAL_MS = 1000

@scheduler_bp.route('/')
@login_required
def index():
    """Render the scheduler dashboard."""
    try:
        # Get all divisions and academic years for dropdowns
        divisions = Division.query.all()
        academic_years = AcademicYear.query.all()
        
        # Get active solver jobs
        active_jobs = []
        from logic.scheduler_logic import active_jobs as job_dict
        for job_id, job in job_dict.items():
            job_info = get_solver_job(job_id)
            job_info['job_id'] = job_id  # Ensure job_id is included
            active_jobs.append(job_info)
        
        # Get constraint categories for configuration
        hard_constraints = HardConstraint.query.all()
        soft_constraints = SoftConstraint.query.all()
        
        # Get scheduling statistics
        stats = get_scheduling_statistics()
        
        return render_template(
            'scheduler.html',
            divisions=divisions,
            academic_years=academic_years,
            active_jobs=active_jobs,
            hard_constraints=hard_constraints,
            soft_constraints=soft_constraints,
            ortools_available=ORTOOLS_AVAILABLE,
            stats=stats,
            polling_interval=POLLING_INTERVAL_MS
        )
    except Exception as e:
        logger.error(f"Error rendering scheduler page: {e}")
        flash(f"An error occurred while loading the scheduler: {str(e)}", "error")
        return redirect(url_for('chatbot.index'))

@scheduler_bp.route('/optimize', methods=['POST'])
@login_required
def optimize_timetable():
    """Start timetable optimization."""
    try:
        # Get parameters from request
        division_id = request.form.get('division_id')
        year_id = request.form.get('year_id')
        time_limit = request.form.get('time_limit', 60)
        
        # Validate inputs
        if division_id:
            try:
                division_id = int(division_id)
                # Verify division exists
                division = Division.query.get(division_id)
                if not division:
                    flash(f"Division with ID {division_id} not found", "error")
                    return redirect(url_for('scheduler.index'))
            except ValueError:
                flash("Invalid division ID", "error")
                return redirect(url_for('scheduler.index'))
        else:
            division_id = None
            
        if year_id:
            # Verify academic year exists
            year = AcademicYear.query.get(year_id)
            if not year:
                flash(f"Academic year with ID {year_id} not found", "error")
                return redirect(url_for('scheduler.index'))
        else:
            year_id = None
            
        # Validate time limit
        try:
            time_limit = int(time_limit)
            if time_limit < 10 or time_limit > 3600:
                time_limit = 60  # Default to 60 seconds if invalid
        except (ValueError, TypeError):
            time_limit = 60
        
        # Check if OR-Tools is available
        solver_type = "OR-Tools" if ORTOOLS_AVAILABLE else "Greedy Algorithm"
        
        # Start optimization
        job_id = solve_timetable(
            current_app._get_current_object(), 
            year_id=year_id, 
            division_id=division_id, 
            time_limit_seconds=time_limit
        )
        
        if job_id:
            flash(f"Optimization started with job ID: {job_id} using {solver_type}. The process will run for up to {time_limit} seconds.", "success")
            return redirect(url_for('scheduler.job_status', job_id=job_id))
        else:
            flash("Failed to start optimization. Check server logs for details.", "error")
            return redirect(url_for('scheduler.index'))
    
    except Exception as e:
        logger.error(f"Error starting optimization: {str(e)}")
        flash(f"Error starting optimization: {str(e)}", "error")
        return redirect(url_for('scheduler.index'))

@scheduler_bp.route('/job/<job_id>')
@login_required
def job_status(job_id):
    """Show detailed status for a specific job."""
    try:
        # Get job details
        job = get_solver_job(job_id)
        
        if job['status'] == "NOT_AVAILABLE":
            flash(f"Job {job_id} not found", "error")
            return redirect(url_for('scheduler.index'))
        
        # Get solution details if available
        solution = None
        from logic.scheduler_logic import active_jobs as job_dict
        if job_id in job_dict and 'solution' in job_dict[job_id]:
            solution = job_dict[job_id]['solution']
        
        # Format statistics
        stats = job.get('stats', {})
        format_stats = {
            'total_lessons': stats.get('total_lessons', 0),
            'scheduled_lessons': stats.get('scheduled_lessons', 0),
            'scheduling_rate': f"{stats.get('scheduling_rate', 0) * 100:.1f}%",
            'objective_value': stats.get('objective_value', 'N/A'),
            'solver_type': stats.get('solver_type', 'Unknown'),
            'duration': f"{stats.get('duration_seconds', 0):.2f} seconds"
        }
        
        return render_template(
            'job_status.html',
            job_id=job_id,
            job=job,
            stats=format_stats,
            solution=solution,
            polling_interval=POLLING_INTERVAL_MS,
            is_completed=job['status'] in ["COMPLETED", "ERROR", "STOPPED", "DATABASE_ERROR"]
        )
    
    except Exception as e:
        logger.error(f"Error viewing job status: {str(e)}")
        flash(f"Error viewing job status: {str(e)}", "error")
        return redirect(url_for('scheduler.index'))

@scheduler_bp.route('/api/job/<job_id>')
@login_required
def get_job_api(job_id):
    """API endpoint for getting job status."""
    try:
        job = get_solver_job(job_id)
        return jsonify(job)
    
    except Exception as e:
        logger.error(f"Error getting job status API: {str(e)}")
        return jsonify({
            'status': 'ERROR',
            'error': str(e)
        }), 500

@scheduler_bp.route('/stop/<job_id>', methods=['POST'])
@login_required
def stop_optimization(job_id):
    """Stop an active optimization job."""
    try:
        success = stop_solving(job_id)
        
        if success:
            flash(f"Optimization job {job_id} stopped successfully", "success")
        else:
            flash(f"Job {job_id} not found or already completed", "warning")
            
        return redirect(url_for('scheduler.job_status', job_id=job_id))
    
    except Exception as e:
        logger.error(f"Error stopping optimization: {str(e)}")
        flash(f"Error stopping optimization: {str(e)}", "error")
        return redirect(url_for('scheduler.index'))

@scheduler_bp.route('/constraints')
@login_required
def list_constraints():
    """List all constraints used in the scheduler."""
    # Get all hard and soft constraints from the database
    hard_constraints = HardConstraint.query.all()
    soft_constraints = SoftConstraint.query.all()
    
    return render_template(
        'constraints.html',
        hard_constraints=hard_constraints,
        soft_constraints=soft_constraints
    )

@scheduler_bp.route('/constraint/hard', methods=['POST'])
@login_required
def add_hard_constraint():
    """Add a new hard constraint."""
    try:
        constraint_type = request.form.get('constraint_type')
        entity_type = request.form.get('entity_type')
        entity_id = request.form.get('entity_id')
        value = request.form.get('value')
        description = request.form.get('description')
        
        # Validate inputs
        if not all([constraint_type, entity_type, entity_id, value]):
            flash("All fields are required", "error")
            return redirect(url_for('scheduler.list_constraints'))
        
        # Create new constraint
        constraint = HardConstraint(
            constraint_type=constraint_type,
            entity_type=entity_type,
            entity_id=entity_id,
            value=value,
            description=description
        )
        
        db.session.add(constraint)
        db.session.commit()
        
        flash(f"Hard constraint added successfully", "success")
        return redirect(url_for('scheduler.list_constraints'))
    
    except Exception as e:
        logger.error(f"Error adding hard constraint: {str(e)}")
        db.session.rollback()
        flash(f"Error adding constraint: {str(e)}", "error")
        return redirect(url_for('scheduler.list_constraints'))

@scheduler_bp.route('/constraint/soft', methods=['POST'])
@login_required
def add_soft_constraint():
    """Add a new soft constraint."""
    try:
        constraint_type = request.form.get('constraint_type')
        entity_type = request.form.get('entity_type')
        entity_id = request.form.get('entity_id')
        value = request.form.get('value')
        weight = request.form.get('weight', 1)
        description = request.form.get('description')
        
        # Validate inputs
        if not all([constraint_type, entity_type, entity_id, value]):
            flash("All fields are required", "error")
            return redirect(url_for('scheduler.list_constraints'))
        
        # Convert weight to integer
        try:
            weight = int(weight)
        except (ValueError, TypeError):
            weight = 1
        
        # Create new constraint
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
        
        flash(f"Soft constraint added successfully", "success")
        return redirect(url_for('scheduler.list_constraints'))
    
    except Exception as e:
        logger.error(f"Error adding soft constraint: {str(e)}")
        db.session.rollback()
        flash(f"Error adding constraint: {str(e)}", "error")
        return redirect(url_for('scheduler.list_constraints'))

@scheduler_bp.route('/constraint/delete/<constraint_type>/<int:constraint_id>', methods=['POST'])
@login_required
def delete_constraint(constraint_type, constraint_id):
    """Delete a constraint."""
    try:
        if constraint_type == 'hard':
            constraint = HardConstraint.query.get(constraint_id)
        elif constraint_type == 'soft':
            constraint = SoftConstraint.query.get(constraint_id)
        else:
            flash("Invalid constraint type", "error")
            return redirect(url_for('scheduler.list_constraints'))
        
        if not constraint:
            flash(f"Constraint with ID {constraint_id} not found", "error")
            return redirect(url_for('scheduler.list_constraints'))
        
        db.session.delete(constraint)
        db.session.commit()
        
        flash(f"{constraint_type.capitalize()} constraint deleted successfully", "success")
        return redirect(url_for('scheduler.list_constraints'))
    
    except Exception as e:
        logger.error(f"Error deleting constraint: {str(e)}")
        db.session.rollback()
        flash(f"Error deleting constraint: {str(e)}", "error")
        return redirect(url_for('scheduler.list_constraints'))

@scheduler_bp.route('/analyze')
@login_required
def analyze_schedule():
    """Analyze the current schedule for potential issues."""
    try:
        from logic.calendar_logic import check_scheduling_conflicts
        
        # Get all events with assigned timeslots and venues
        events = db.session.query(Event).filter(
            Event.day_of_week.isnot(None),
            Event.start_time.isnot(None),
            Event.end_time.isnot(None),
            Event.venue_id.isnot(None)
        ).all()
        
        # Initialize conflicts structure
        all_conflicts = {
            'room_conflicts': [],
            'teacher_conflicts': [],
            'student_group_conflicts': []
        }
        
        # Check each event for conflicts
        for event in events:
            conflicts = check_scheduling_conflicts(event, events)
            
            if conflicts['has_conflicts']:
                # Add room conflicts
                for conflict_event in conflicts['venue_conflicts']:
                    all_conflicts['room_conflicts'].append({
                        'event1': event,
                        'event2': conflict_event,
                        'room': event.venue,
                        'day': day_name(event.day_of_week)
                    })
                
                # Add teacher conflicts
                for conflict_event in conflicts['teacher_conflicts']:
                    all_conflicts['teacher_conflicts'].append({
                        'event1': event,
                        'event2': conflict_event,
                        'teacher': event.teacher,
                        'day': day_name(event.day_of_week)
                    })
                
                # Add student group conflicts
                for conflict_event in conflicts['division_conflicts']:
                    all_conflicts['student_group_conflicts'].append({
                        'event1': event,
                        'event2': conflict_event,
                        'division': event.division,
                        'day': day_name(event.day_of_week)
                    })
        
        # Get statistics
        stats = {
            'total_events': len(events),
            'room_conflicts': len(all_conflicts['room_conflicts']),
            'teacher_conflicts': len(all_conflicts['teacher_conflicts']),
            'student_group_conflicts': len(all_conflicts['student_group_conflicts']),
            'total_conflicts': len(all_conflicts['room_conflicts']) + 
                              len(all_conflicts['teacher_conflicts']) + 
                              len(all_conflicts['student_group_conflicts'])
        }
        
        return render_template(
            'analysis.html',
            conflicts=all_conflicts,
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Error analyzing schedule: {str(e)}")
        flash(f"Error analyzing schedule: {str(e)}", "error")
        return redirect(url_for('scheduler.index'))

def day_name(day_index):
    """Convert day index to day name."""
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if 0 <= day_index < len(day_names):
        return day_names[day_index]
    return "Unknown"

# Initialize scheduler when blueprint is registered
@scheduler_bp.record_once
def initialize_scheduler(state):
    """Initialize the scheduler when the blueprint is registered."""
    try:
        # Get the Flask app from the state
        app = state.app
        
        # Clean up any old solver jobs within app context
        with app.app_context():
            try:
                cleanup_old_jobs(24)
            except Exception as e:
                logger.warning(f"Initial cleanup failed: {e}")
        
        # Start the maintenance thread with the app instance
        maintenance_thread = threading.Thread(
            target=maintenance_worker, 
            args=(app,),
            daemon=True
        )
        maintenance_thread.start()
        
        logger.info("Scheduler initialization complete")
    except Exception as e:
        logger.error(f"Error initializing scheduler: {e}")

def maintenance_worker(app):
    """Worker function for maintenance tasks that requires app context."""
    while True:
        try:
            # Use the passed app instance for the context
            with app.app_context():
                # Clean up old jobs
                cleanup_old_jobs(24)
                
                # Get system statistics
                try:
                    stats = get_scheduling_statistics()
                    if stats and 'events' in stats:
                        logger.info(f"System stats: {stats['events']['total']} total events, "
                                    f"{stats['events']['scheduled']} scheduled "
                                    f"({stats['events']['scheduling_rate']*100:.1f}%)")
                    else:
                        logger.info("System stats not available")
                except Exception as stats_err:
                    logger.error(f"Error getting system stats: {stats_err}")
        
        except Exception as e:
            logger.error(f"Error in maintenance worker: {e}")
        
        # Sleep for 15 minutes before next check
        time.sleep(15 * 60)