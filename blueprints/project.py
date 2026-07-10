import os
import re
import io
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, send_file
from database.db import execute_read, execute_write

project_bp = Blueprint('project', __name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-()]{10,20}$')

@project_bp.route('/projects')
def catalog():
    """Renders the project catalog page, loading projects dynamically with search and pagination."""
    # 1. Retrieve query parameters
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
        
    per_page = 6
    offset = (page - 1) * per_page
    
    # 2. Build parameterized queries
    placeholder = '%s'
    query = "SELECT * FROM projects WHERE status = 'Active'"
    count_query = "SELECT COUNT(*) FROM projects WHERE status = 'Active'"
    params = []
    count_params = []
    
    if search_query:
        search_clause = " AND (title ILIKE %s OR description ILIKE %s OR technologies ILIKE %s OR category ILIKE %s)"
        query += search_clause
        count_query += search_clause
        search_param = f"%{search_query}%"
        params.extend([search_param, search_param, search_param, search_param])
        count_params.extend([search_param, search_param, search_param, search_param])
        
    if category_filter:
        category_clause = " AND category = %s"
        query += category_clause
        count_query += category_clause
        params.append(category_filter)
        count_params.append(category_filter)
        
    query += " ORDER BY id ASC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    
    try:
        # Execute database queries
        projects = execute_read(query, tuple(params))
        total_count_row = execute_read(count_query, tuple(count_params))
        total_count = total_count_row[0]['count'] if total_count_row else 0
    except Exception as e:
        projects = []
        total_count = 0
        print(f"Error querying projects catalog: {e}")
        
    import math
    total_pages = math.ceil(total_count / per_page)
    
    return render_template(
        'projects.html', 
        projects=projects,
        q=search_query,
        category=category_filter,
        page=page,
        total_pages=total_pages,
        total_count=total_count
    )

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
        
        # Trigger Automated WhatsApp Alerts to Student & Coordinator
        try:
            from utils.whatsapp import send_whatsapp_booking_alerts
            price_formatted = f"INR {project['price']:,}"
            send_whatsapp_booking_alerts(
                student_name=name,
                student_phone=phone,
                project_title=project['title'],
                price_formatted=price_formatted,
                referral_code=ref_code_cleaned
            )
        except Exception as ws_err:
            print(f"WhatsApp Dispatch Warning: {ws_err}")
        
        return jsonify({
            'success': True,
            'message': 'Project Demo Booking Successful!',
            'project_title': project['title'],
            'student_name': name,
            'phone': phone
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server Error saving booking: {e}'}), 500

@project_bp.route('/tools/research-agent')
def research_agent_workspace():
    """Renders the interactive AI Research Agent workspace page."""
    return render_template('tools/research_agent.html')

@project_bp.route('/tools/research-agent/run', methods=['POST'])
def run_research():
    """Triggers the autonomous search & LLaMA synthesis pipeline."""
    from blueprints.research_agent import research_agent
    
    data = request.get_json(force=True, silent=True) or {}
    topic = data.get('topic', '').strip()
    depth = data.get('depth', 'quick').lower()
    
    if not topic:
        return jsonify({'success': False, 'error': 'Please enter a research topic.'}), 400
        
    if len(topic) > 300:
        return jsonify({'success': False, 'error': 'Topic is too long. Max 300 characters.'}), 400
        
    if depth not in {'quick', 'deep', 'expert'}:
        depth = 'quick'
        
    try:
        result = research_agent(topic, depth=depth)
        return jsonify({
            'success': True,
            'filename': result['filename'],
            'report': result['report'],
            'sources': result['sources'],
            'depth': result['depth'],
            'model_used': result.get('model_used', 'unknown')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@project_bp.route('/tools/research-agent/download/<filename>')
def download_txt_report(filename):
    """Downloads the saved raw text research report."""
    from blueprints.research_agent import REPORTS_DIR
    
    safe_name = os.path.basename(filename)
    filepath = os.path.join(REPORTS_DIR, safe_name)
    
    if not os.path.exists(filepath):
        from flask import abort
        abort(404)
        
    return send_file(filepath, as_attachment=True)

@project_bp.route('/tools/research-agent/download-pdf/<filename>')
def download_pdf_report(filename):
    """Downloads the dynamic compiled, logo-branded PDF version of the report."""
    from blueprints.research_agent import REPORTS_DIR
    from blueprints.pdf_generator import generate_pdf
    
    safe_name = os.path.basename(filename)
    # Target saved txt report filename
    txt_filename = safe_name.replace('.pdf', '-report.txt').replace('-report-report.txt', '-report.txt')
    if not txt_filename.endswith('.txt'):
        txt_filename = safe_name + '-report.txt'
        
    # Standard replacement rules
    if '-report.txt' not in txt_filename:
        txt_filename = txt_filename.replace('.txt', '') + '-report.txt'

    filepath = os.path.join(REPORTS_DIR, txt_filename)
    # Check fallback naming if direct lookup fails
    if not os.path.exists(filepath):
        # Scan dir for fuzzy match
        for f in os.listdir(REPORTS_DIR):
            if f.lower().startswith(safe_name.split('-report')[0].lower()):
                filepath = os.path.join(REPORTS_DIR, f)
                break
                
    if not os.path.exists(filepath):
        from flask import abort
        abort(404)
        
    with open(filepath, 'r', encoding='utf-8') as f:
        report_text = f.read()
        
    # Extract topic from header
    topic = "Research Report"
    try:
        first_line = report_text.split('\n')[0]
        if first_line.startswith("Research Report: "):
            topic = first_line.replace("Research Report: ", "").strip()
    except Exception:
        pass
        
    # Extract report body content (strip prefix divider)
    body_text = report_text
    if "==================================================" in body_text:
        body_text = body_text.split("==================================================")[1].strip()
        
    try:
        pdf_bytes = generate_pdf(topic, body_text)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=safe_name.replace('.txt', '.pdf').replace('.pdf.pdf', '.pdf')
        )
    except Exception as e:
        return jsonify({'success': False, 'error': f"Failed to generate PDF: {str(e)}"}), 500

def slugify(text):
    """Utility to convert text to SEO-friendly slug strings."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

@project_bp.app_template_filter('slugify')
def slugify_filter(s):
    return slugify(s)

@project_bp.route('/projects/<int:project_id>-<string:slug>')
def details(project_id, slug):
    """Renders the detailed SEO landing page for a specific project."""
    try:
        # Fetch target project
        rows = execute_read("SELECT * FROM projects WHERE id = %s AND status = 'Active'", (project_id,))
        if not rows:
            flash("Project not found in our catalog.", "error")
            return redirect(url_for('project.catalog'))
            
        project = rows[0]
        
        # Enforce canonical SEO URLs (redirect if slug is mismatched)
        expected_slug = slugify(project['title'])
        if slug != expected_slug:
            return redirect(url_for('project.details', project_id=project_id, slug=expected_slug), code=301)
            
        # Fetch related projects (same category, excluding current one) for internal linking
        related = execute_read(
            "SELECT * FROM projects WHERE category = %s AND id != %s AND status = 'Active' LIMIT 3",
            (project['category'], project_id)
        )
    except Exception as e:
        print(f"Error querying project details: {e}")
        flash("An error occurred while loading project details.", "error")
        return redirect(url_for('project.catalog'))
        
    return render_template('project_detail.html', project=project, related=related)

@project_bp.route('/projects/custom-submit', methods=['POST'])
def custom_submit():
    """Accepts custom project requirements requests from students."""
    if request.is_json:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        department = data.get('department', '').strip()
        topic = data.get('topic', '').strip()
        requirements = data.get('requirements', '').strip()
        deadline = data.get('deadline', '').strip()
    else:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        topic = request.form.get('topic', '').strip()
        requirements = request.form.get('requirements', '').strip()
        deadline = request.form.get('deadline', '').strip()

    # Validations
    if not name or not email or not phone or not department or not topic or not requirements:
        return jsonify({'success': False, 'message': 'Please fill out all required fields.'}), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400

    if not PHONE_REGEX.match(phone):
        return jsonify({'success': False, 'message': 'Please enter a valid WhatsApp phone number.'}), 400

    # Insert into database
    try:
        query = """
        INSERT INTO custom_requests (name, email, phone, department, topic, requirements, deadline, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
        """
        execute_write(query, (name, email, phone, department, topic, requirements, deadline))
        
        return jsonify({
            'success': True,
            'message': 'Custom Project Requirements Submitted Successfully!',
            'student_name': name,
            'topic': topic,
            'department': department,
            'phone': phone
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server Error saving custom request: {e}'}), 500
