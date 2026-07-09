import re
import json
import random
import urllib.request
from functools import wraps
from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, session, current_app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import execute_read, execute_write

ambassador_bp = Blueprint('ambassador', __name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-()]{10,20}$')

def ambassador_required(f):
    """Decorator to enforce ambassador authentication on routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('ambassador_id'):
            flash("Please log in with your email and password first.", "error")
            return redirect(url_for('ambassador.login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_unique_code(name):
    """Generates a unique referral code GTV-AMB-[FIRST_NAME]-[RANDOM_4_DIGITS] and verifies it against the DB."""
    first_name = name.strip().split()[0]
    first_name_clean = ''.join(char for char in first_name if char.isalpha()).upper()
    if not first_name_clean:
        first_name_clean = "LEAD"
        
    while True:
        rand_num = random.randint(1000, 9999)
        candidate_code = f"GTV-AMB-{first_name_clean}-{rand_num}"
        
        # Check uniqueness in DB
        rows = execute_read("SELECT id FROM ambassadors WHERE referral_code = %s", (candidate_code,))
        if not rows:
            return candidate_code

def verify_google_token(id_token):
    """Securely verifies a Google Sign-In JWT token using Google's tokeninfo API."""
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        current_app.logger.warning(f"Google Token Verification Failed: {e}")
        return None

@ambassador_bp.route('/ambassadors/join', methods=['GET', 'POST'])
def join():
    """Handles both Google-onboarded and Traditional Ambassador applications."""
    # Check if this is a Google onboarding session (pre-filled details)
    google_name = session.get('google_onboarding_name', '')
    google_email = session.get('google_onboarding_email', '')
    is_google_signup = bool(google_email)
    google_client_id = current_app.config.get('GOOGLE_CLIENT_ID', 'placeholder-google-client-id')
    
    if request.method == 'POST':
        # Retrieve form data
        phone = request.form.get('phone', '').strip()
        college = request.form.get('college', '').strip()
        payment_info = request.form.get('payment_info', '').strip()
        
        if is_google_signup:
            # Name and Email are locked from their verified Google session
            name = google_name
            email = google_email
            password = None
        else:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            
        # Validation checks
        errors = []
        if not name or len(name) < 2:
            errors.append("Please provide your full name.")
        if not email or not EMAIL_REGEX.match(email):
            errors.append("Please provide a valid email address.")
        if not phone or not PHONE_REGEX.match(phone):
            errors.append("Please provide a valid phone number (10 to 20 digits).")
        if not college or len(college) < 3:
            errors.append("Please provide your college name.")
        if not payment_info or len(payment_info) < 5:
            errors.append("Please provide valid UPI or payment info.")
            
        # Password validation for traditional signups
        if not is_google_signup:
            if not password or len(password) < 6:
                errors.append("Password must be at least 6 characters long.")
                
        # Check duplicate email
        if not errors:
            rows = execute_read("SELECT id FROM ambassadors WHERE email = %s", (email,))
            if rows:
                errors.append("An application with this email address already exists. Please log in.")
                
        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template(
                'ambassadors/join.html', 
                name=name, email=email, phone=phone, college=college, payment_info=payment_info,
                is_google_signup=is_google_signup, google_name=google_name, google_email=google_email,
                google_client_id=google_client_id
            )
            
        # Encrypt password for traditional signups
        password_hash = generate_password_hash(password) if password else None
        
        # Save to DB
        try:
            referral_code = generate_unique_code(name)
            query = """
            INSERT INTO ambassadors (name, email, phone, college, payment_info, referral_code, password_hash, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Approved')
            """
            execute_write(query, (name, email, phone, college, payment_info, referral_code, password_hash))
            
            # Clear google session variables
            session.pop('google_onboarding_name', None)
            session.pop('google_onboarding_email', None)
            
            # Retrieve ID to authenticate session and redirect
            rows = execute_read("SELECT id FROM ambassadors WHERE email = %s", (email,))
            if rows:
                amb_id = rows[0]['id']
                session['ambassador_id'] = amb_id
                flash("Congratulations! Your account is active. Your Offer Letter is ready.", "success")
                return redirect(url_for('ambassador.welcome', amb_id=amb_id))
        except Exception as e:
            flash(f"System Error during registration: {e}", "error")
            
    return render_template(
        'ambassadors/join.html',
        is_google_signup=is_google_signup,
        google_name=google_name,
        google_email=google_email,
        google_client_id=google_client_id
    )

@ambassador_bp.route('/ambassadors/login', methods=['GET', 'POST'])
def login():
    """Handles traditional Email & Password authentication."""
    if session.get('ambassador_id'):
        return redirect(url_for('ambassador.dashboard'))
        
    google_client_id = current_app.config.get('GOOGLE_CLIENT_ID', 'placeholder-google-client-id')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template('ambassadors/login.html', email=email, google_client_id=google_client_id)
            
        rows = execute_read("SELECT * FROM ambassadors WHERE email = %s", (email,))
        if rows:
            record = rows[0]
            # Check if this user has set a password (they might have registered via Google only)
            if not record.get('password_hash'):
                flash("This account was registered using Google Sign-In. Please click the 'Sign in with Google' button.", "error")
                return render_template('ambassadors/login.html', email=email, google_client_id=google_client_id)
                
            if check_password_hash(record['password_hash'], password):
                session['ambassador_id'] = record['id']
                flash("Welcome back to your Ambassador Dashboard.", "success")
                return redirect(url_for('ambassador.dashboard'))
            
        flash("Invalid email or password. Please verify your credentials.", "error")
            
    return render_template('ambassadors/login.html', google_client_id=google_client_id)

@ambassador_bp.route('/ambassadors/google-auth', methods=['POST'])
def google_auth():
    """Receives and verifies Google OAuth JWT credentials from frontend, logging them in or initiating onboarding."""
    data = request.get_json() or {}
    id_token = data.get('credential', '')
    
    if not id_token:
        return jsonify({'success': False, 'message': 'Missing Google auth credentials.'}), 400
        
    # Verify the token with Google APIs
    verified_payload = verify_google_token(id_token)
    if not verified_payload:
        return jsonify({'success': False, 'message': 'Failed cryptographical validation of Google ID Token.'}), 400
        
    email = verified_payload.get('email', '').strip()
    name = verified_payload.get('name', '').strip()
    
    if not email:
        return jsonify({'success': False, 'message': 'Google account profile does not contain a valid email address.'}), 400
        
    # Search database for this email
    rows = execute_read("SELECT id FROM ambassadors WHERE email = %s", (email,))
    if rows:
        # User already exists - Log them in immediately!
        session['ambassador_id'] = rows[0]['id']
        return jsonify({
            'success': True,
            'action': 'login',
            'redirect': url_for('ambassador.dashboard')
        })
    else:
        # New User - Save Google profile info in session and redirect to onboarding join page
        session['google_onboarding_name'] = name
        session['google_onboarding_email'] = email
        return jsonify({
            'success': True,
            'action': 'onboard',
            'redirect': url_for('ambassador.join')
        })

@ambassador_bp.route('/ambassadors/logout')
def logout():
    """Logs out the ambassador and clears sessions."""
    session.pop('ambassador_id', None)
    session.pop('google_onboarding_name', None)
    session.pop('google_onboarding_email', None)
    flash("Session terminated successfully. You have logged out.", "success")
    return redirect(url_for('ambassador.login'))

@ambassador_bp.route('/ambassadors/dashboard')
@ambassador_required
def dashboard():
    """Displays ambassador's live stats, referral grid, and payout UPI details."""
    amb_id = session.get('ambassador_id')
    rows = execute_read("SELECT * FROM ambassadors WHERE id = %s", (amb_id,))
    if not rows:
        session.pop('ambassador_id', None)
        return redirect(url_for('ambassador.login'))
        
    ambassador = dict(rows[0])
    
    # Fetch referred contact inquiries (Leads)
    leads = execute_read(
        "SELECT name, subject, created_at FROM contacts WHERE referral_code = %s ORDER BY created_at DESC",
        (ambassador['referral_code'],)
    )
    
    # Fetch referred project bookings (Sales)
    bookings = execute_read(
        "SELECT b.name, b.project_title, b.status, b.created_at, p.price FROM bookings b JOIN projects p ON b.project_id = p.id WHERE b.referral_code = %s ORDER BY b.created_at DESC",
        (ambassador['referral_code'],)
    )
    
    # Calculate 15% commission of Approved/finalized sales
    approved_sales = [b for b in bookings if b['status'] == 'Approved']
    total_earnings = sum(int(b['price'] * 0.15) for b in approved_sales)
    
    created_at = ambassador.get('created_at')
    if hasattr(created_at, 'strftime'):
        formatted_date = created_at.strftime('%B %d, %Y')
    else:
        try:
            formatted_date = str(created_at).split()[0]
        except Exception:
            formatted_date = str(created_at)
            
    return render_template(
        'ambassadors/dashboard.html',
        ambassador=ambassador,
        leads=leads,
        leads_count=len(leads),
        bookings=bookings,
        bookings_count=len(bookings),
        approved_bookings_count=len(approved_sales),
        total_earnings=total_earnings,
        formatted_date=formatted_date
    )

@ambassador_bp.route('/ambassadors/welcome/<int:amb_id>')
def welcome(amb_id):
    """Renders the printable, official Appointment/Offer Letter for the ambassador."""
    rows = execute_read("SELECT * FROM ambassadors WHERE id = %s", (amb_id,))
    if not rows:
        abort(404)
        
    ambassador = dict(rows[0])
    created_at = ambassador.get('created_at')
    
    if hasattr(created_at, 'strftime'):
        formatted_date = created_at.strftime('%B %d, %Y')
    else:
        try:
            formatted_date = str(created_at).split()[0]
        except Exception:
            formatted_date = str(created_at)
            
    return render_template('ambassadors/offer_letter.html', ambassador=ambassador, formatted_date=formatted_date)
