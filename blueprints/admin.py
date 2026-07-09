import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from database.db import execute_read, execute_write

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to enforce administrator authentication on routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Unauthorized access. Please log in first.", "error")
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles admin login screen and credentials verification."""
    # If already logged in, redirect directly to dashboard
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        expected_user = current_app.config.get('ADMIN_USERNAME')
        expected_pass = current_app.config.get('ADMIN_PASSWORD')
        
        if username == expected_user and password == expected_pass:
            session['admin_logged_in'] = True
            flash("Welcome back, Administrator. Session authorized.", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid administrative credentials. Please verify username and password.", "error")
            
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Logs out the administrator by clearing session variables."""
    session.pop('admin_logged_in', None)
    flash("Session terminated successfully. You have logged out.", "success")
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Renders the admin control dashboard displaying metrics, messages, subscribers, jobs, applications, ambassadors, and bookings."""
    try:
        # Fetch statistics counts and lists
        contacts = execute_read("SELECT * FROM contacts ORDER BY created_at DESC")
        subscribers = execute_read("SELECT * FROM newsletter ORDER BY created_at DESC")
        jobs = execute_read("SELECT * FROM jobs ORDER BY created_at DESC")
        applications = execute_read("SELECT * FROM applications ORDER BY created_at DESC")
        ambassadors = execute_read("SELECT * FROM ambassadors ORDER BY created_at DESC")
        bookings = execute_read("SELECT * FROM bookings ORDER BY created_at DESC")
        
        return render_template(
            'admin/dashboard.html',
            contacts=contacts,
            subscribers=subscribers,
            jobs=jobs,
            applications=applications,
            ambassadors=ambassadors,
            bookings=bookings,
            contacts_count=len(contacts),
            subscribers_count=len(subscribers),
            jobs_count=len(jobs),
            applications_count=len(applications),
            ambassadors_count=len(ambassadors),
            bookings_count=len(bookings)
        )
    except Exception as e:
        current_app.logger.error(f"Admin Dashboard Error: {e}")
        flash("Failed to retrieve dashboard datasets from database.", "error")
        return render_template(
            'admin/dashboard.html',
            contacts=[],
            subscribers=[],
            jobs=[],
            applications=[],
            ambassadors=[],
            bookings=[],
            contacts_count=0,
            subscribers_count=0,
            jobs_count=0,
            applications_count=0,
            ambassadors_count=0,
            bookings_count=0
        )

@admin_bp.route('/contacts/delete/<int:contact_id>', methods=['POST'])
@admin_required
def delete_contact(contact_id):
    """Deletes a contact submission request by ID."""
    try:
        execute_write("DELETE FROM contacts WHERE id = %s", (contact_id,))
        flash("Contact inquiry purged successfully.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to purge contact: {e}")
        flash("Database deletion error. Failed to purge contact inquiry.", "error")
        
    return redirect(url_for('admin.dashboard', _anchor='contacts'))

@admin_bp.route('/jobs/create', methods=['POST'])
@admin_required
def create_job():
    """Processes validation and inserts a new job posting into the database."""
    title = request.form.get('title', '').strip()
    department = request.form.get('department', '').strip()
    location = request.form.get('location', '').strip()
    job_type = request.form.get('type', '').strip()
    description = request.form.get('description', '').strip()
    requirements = request.form.get('requirements', '').strip()
    
    # Validation checks
    errors = []
    if not title or len(title) < 3:
        errors.append("Job title is required (min 3 characters).")
    if not department or len(department) < 2:
        errors.append("Department is required.")
    if not location or len(location) < 2:
        errors.append("Location is required.")
    if not job_type:
        errors.append("Job type is required.")
    if not description or len(description) < 10:
        errors.append("Job description is required (min 10 characters).")
    if not requirements or len(requirements) < 5:
        errors.append("Key requirements are required.")
        
    if errors:
        for err in errors:
            flash(err, "error")
        return redirect(url_for('admin.dashboard', _anchor='jobs'))
        
    try:
        query = """
        INSERT INTO jobs (title, department, location, type, description, requirements)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_write(query, (title, department, location, job_type, description, requirements))
        flash("New job posting added dynamically to the careers portal.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to create job posting: {e}")
        flash("Database insertion error. Failed to post job opening.", "error")
        
    return redirect(url_for('admin.dashboard', _anchor='jobs'))

@admin_bp.route('/jobs/delete/<int:job_id>', methods=['POST'])
@admin_required
def delete_job(job_id):
    """Deletes a job posting from the database by ID."""
    try:
        execute_write("DELETE FROM jobs WHERE id = %s", (job_id,))
        flash("Job opening deleted from careers portal successfully.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to delete job: {e}")
        flash("Database deletion error. Failed to delete job opening.", "error")
        
    return redirect(url_for('admin.dashboard', _anchor='jobs'))

@admin_bp.route('/applications/delete/<int:app_id>', methods=['POST'])
@admin_required
def delete_application(app_id):
    """Deletes a candidate application record and its uploaded resume file."""
    try:
        # Fetch the resume filepath to delete it from local storage
        rows = execute_read("SELECT resume_path FROM applications WHERE id = %s", (app_id,))
        if rows:
            resume_path = rows[0]['resume_path']
            # resume_path has pattern: /static/uploads/filename
            filename = resume_path.split('/')[-1]
            full_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                current_app.logger.info(f"Admin: Purged resume file: {full_path}")
        
        # Purge record from database
        execute_write("DELETE FROM applications WHERE id = %s", (app_id,))
        flash("Candidate application purged successfully.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to delete candidate application: {e}")
        flash("Failed to delete candidate application.", "error")
        
    return redirect(url_for('admin.dashboard', _anchor='applications'))

@admin_bp.route('/ambassadors/delete/<int:amb_id>', methods=['POST'])
@admin_required
def delete_ambassador(amb_id):
    """Permanently deletes an ambassador registration record by ID."""
    try:
        execute_write("DELETE FROM ambassadors WHERE id = %s", (amb_id,))
        flash("Ambassador record permanently purged from database.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to delete ambassador: {e}")
        flash("Failed to delete ambassador record.", "error")
        
    return redirect(url_for('admin.dashboard', _anchor='ambassadors'))

@admin_bp.route('/bookings/approve/<int:booking_id>', methods=['POST'])
@admin_required
def approve_booking(booking_id):
    """Approves a demo booking/order request once payment is completed."""
    try:
        execute_write("UPDATE bookings SET status = 'Approved' WHERE id = %s", (booking_id,))
        flash("Booking approved successfully. Ambassador commission credited.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to approve booking: {e}")
        flash("Failed to approve project booking.", "error")
        
    return redirect(url_for('admin.dashboard', _anchor='bookings'))

@admin_bp.route('/bookings/delete/<int:booking_id>', methods=['POST'])
@admin_required
def delete_booking(booking_id):
    """Deletes or rejects a booking/order request."""
    try:
        execute_write("DELETE FROM bookings WHERE id = %s", (booking_id,))
        flash("Project booking record deleted successfully.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to delete booking: {e}")
        flash("Failed to delete project booking.", "error")
        
    return redirect(url_for('admin.dashboard', _anchor='bookings'))
