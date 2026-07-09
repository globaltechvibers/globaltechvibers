import re
import os
import uuid
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from database.db import execute_write, execute_read

contact_bp = Blueprint('contact', __name__)

# Regular expressions for validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-()]{10,20}$')

def validate_contact_form(name, email, phone, subject, message):
    """Validates the input parameters for the contact form."""
    errors = []
    
    # Validate Name
    if not name or len(name.strip()) < 2 or len(name.strip()) > 100:
        errors.append("Name must be between 2 and 100 characters.")
        
    # Validate Email
    if not email or not EMAIL_REGEX.match(email.strip()):
        errors.append("Please provide a valid email address.")
        
    # Validate Phone
    if not phone or not PHONE_REGEX.match(phone.strip()):
        errors.append("Please provide a valid phone number (10 to 20 digits).")
        
    # Validate Subject
    if not subject or len(subject.strip()) < 3 or len(subject.strip()) > 150:
        errors.append("Subject must be between 3 and 150 characters.")
        
    # Validate Message
    if not message or len(message.strip()) < 10 or len(message.strip()) > 3000:
        errors.append("Message must be between 10 and 3000 characters.")
        
    return errors

@contact_bp.route('/contact/submit', methods=['POST'])
def submit_contact():
    """Handles submission of contact forms (supports standard POST and AJAX)."""
    # Fetch parameters from JSON or Form POST
    if request.is_json:
        data = request.get_json() or {}
        name = data.get('name', '')
        email = data.get('email', '')
        phone = data.get('phone', '')
        subject = data.get('subject', '')
        message = data.get('message', '')
        is_ajax = True
    else:
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        subject = request.form.get('subject', '')
        message = request.form.get('message', '')
        is_ajax = False

    # Validate inputs
    errors = validate_contact_form(name, email, phone, subject, message)
    if errors:
        if is_ajax:
            return jsonify({'success': False, 'errors': errors}), 400
        else:
            for err in errors:
                flash(err, 'error')
            return redirect(url_for('main.contact'))

    # Store in database
    try:
        query = """
        INSERT INTO contacts (name, email, phone, subject, message) 
        VALUES (%s, %s, %s, %s, %s)
        """
        execute_write(query, (name.strip(), email.strip(), phone.strip(), subject.strip(), message.strip()))
        
        success_msg = "Thank you! Your message has been sent successfully. We will contact you soon."
        if is_ajax:
            return jsonify({'success': True, 'message': success_msg}), 200
        else:
            flash(success_msg, 'success')
            return redirect(url_for('main.contact'))
    except Exception as e:
        error_msg = "A server error occurred while processing your request. Please try again later."
        if is_ajax:
            return jsonify({'success': False, 'errors': [error_msg]}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('main.contact'))

@contact_bp.route('/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Handles newsletter email subscription requests."""
    if request.is_json:
        data = request.get_json() or {}
        email = data.get('email', '')
        is_ajax = True
    else:
        email = request.form.get('email', '')
        is_ajax = False

    email = email.strip()
    
    # Validate email
    if not email or not EMAIL_REGEX.match(email):
        err_msg = "Please enter a valid email address."
        if is_ajax:
            return jsonify({'success': False, 'message': err_msg}), 400
        else:
            flash(err_msg, 'error')
            return redirect(request.referrer or url_for('main.index'))

    try:
        # Check if email already registered
        existing = execute_read("SELECT id FROM newsletter WHERE email = %s", (email,))
        if existing:
            warn_msg = "This email is already subscribed to our newsletter."
            if is_ajax:
                return jsonify({'success': True, 'message': warn_msg}), 200
            else:
                flash(warn_msg, 'info')
                return redirect(request.referrer or url_for('main.index'))
                
        # Insert registration
        execute_write("INSERT INTO newsletter (email) VALUES (%s)", (email,))
        success_msg = "Successfully subscribed! Thank you for staying connected."
        if is_ajax:
            return jsonify({'success': True, 'message': success_msg}), 200
        else:
            flash(success_msg, 'success')
            return redirect(request.referrer or url_for('main.index'))
    except Exception as e:
        error_msg = "Failed to complete subscription. Please try again later."
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(request.referrer or url_for('main.index'))

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@contact_bp.route('/careers/apply', methods=['POST'])
def apply_job():
    """Processes application submissions from candidates for open listings."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    cover_letter = request.form.get('cover_letter', '').strip()
    job_id = request.form.get('job_id', '').strip()
    
    # Check if job exists
    if not job_id:
        return jsonify({'success': False, 'errors': ['Job reference is required.']}), 400
        
    try:
        job_rows = execute_read("SELECT title FROM jobs WHERE id = %s", (job_id,))
        if not job_rows:
            return jsonify({'success': False, 'errors': ['The selected job listing no longer exists.']}), 400
        job_title = job_rows[0]['title']
    except Exception as e:
        current_app.logger.error(f"Careers apply DB search error: {e}")
        return jsonify({'success': False, 'errors': ['Database verification error.']}), 500
    
    # Validation checks
    errors = []
    if not name or len(name) < 2:
        errors.append("Name must be at least 2 characters.")
    if not email or not EMAIL_REGEX.match(email):
        errors.append("Please enter a valid email address.")
    if not phone or not PHONE_REGEX.match(phone):
        errors.append("Please enter a valid phone number (10-20 digits).")
    if not cover_letter or len(cover_letter) < 10:
        errors.append("Cover letter must be at least 10 characters.")
        
    # File upload checks
    if 'resume' not in request.files:
        errors.append("Resume file is required.")
    else:
        file = request.files['resume']
        if file.filename == '':
            errors.append("No resume file selected.")
        elif not allowed_file(file.filename):
            errors.append("Only PDF and DOCX files are allowed.")
            
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400
        
    # Save the file securely and write to DB
    try:
        file = request.files['resume']
        unique_prefix = uuid.uuid4().hex[:8]
        filename = f"{unique_prefix}_{secure_filename(file.filename)}"
        
        # Save path configuration
        uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, filename)
        file.save(file_path)
        
        db_resume_path = f"/static/uploads/{filename}"
        
        query = """
        INSERT INTO applications (job_id, job_title, name, email, phone, resume_path, cover_letter)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        execute_write(query, (job_id, job_title, name, email, phone, db_resume_path, cover_letter))
        
        return jsonify({
            'success': True, 
            'message': 'Application submitted successfully! Our recruitment team will review your resume.'
        }), 200
    except Exception as e:
        current_app.logger.error(f"Application Submission Error: {e}")
        return jsonify({'success': False, 'errors': ['Failed to process application. Please try again later.']}), 500
