import re
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from database.db import execute_read, execute_write

project_bp = Blueprint('project', __name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-()]{10,20}$')

@project_bp.route('/projects')
def catalog():
    """Renders the project catalog page, loading projects dynamically from the database."""
    try:
        # Fetch all active projects
        projects = execute_read("SELECT * FROM projects WHERE status = 'Active' ORDER BY id ASC")
    except Exception as e:
        projects = []
        # Fallback if connection fails
        print(f"Error querying projects catalog: {e}")
        
    return render_template('projects.html', projects=projects)

@project_bp.route('/projects/book', methods=['POST'])
def book():
    """Accepts project demo booking requests."""
    # Check if request is JSON (AJAX)
    if request.is_json:
        data = request.get_json() or {}
        project_id = data.get('project_id')
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        referral_code = data.get('referral_code', '').strip().upper()
    else:
        project_id = request.form.get('project_id')
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        referral_code = request.form.get('referral_code', '').strip().upper()

    # Basic validations
    if not project_id or not name or not email or not phone:
        return jsonify({'success': False, 'message': 'Please fill out all required fields.'}), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400

    if not PHONE_REGEX.match(phone):
        return jsonify({'success': False, 'message': 'Please enter a valid WhatsApp phone number (10-20 digits).'}), 400

    # Fetch project details
    rows = execute_read("SELECT title, price FROM projects WHERE id = %s", (project_id,))
    if not rows:
        return jsonify({'success': False, 'message': 'Project not found in catalog.'}), 404

    project = rows[0]

    # Validate referral code if provided
    ref_code_cleaned = None
    if referral_code:
        amb_rows = execute_read("SELECT id FROM ambassadors WHERE referral_code = %s", (referral_code,))
        if amb_rows:
            ref_code_cleaned = referral_code
        else:
            return jsonify({'success': False, 'message': 'Invalid Ambassador Referral Code. Please check or leave empty.'}), 400

    # Create Booking
    try:
        query = """
        INSERT INTO bookings (project_id, project_title, name, email, phone, referral_code, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
        """
        execute_write(query, (
            project_id,
            project['title'],
            name,
            email,
            phone,
            ref_code_cleaned
        ))
        
        return jsonify({
            'success': True,
            'message': 'Project Demo Booking Successful!',
            'project_title': project['title'],
            'student_name': name,
            'phone': phone
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server Error saving booking: {e}'}), 500
