import re
import random
from functools import wraps
from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, session
from database.db import execute_read, execute_write

ambassador_bp = Blueprint('ambassador', __name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-()]{10,20}$')

def ambassador_required(f):
    """Decorator to enforce ambassador authentication on routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('ambassador_id'):
            flash("Please log in with your email and referral code first.", "error")
            return redirect(url_for('ambassador.login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_unique_code(name):
    """Generates a unique referral code GTV-AMB-[FIRST_NAME]-[RANDOM_4_DIGITS] and verifies it against the DB."""
    # Clean first name to alphabetic characters, uppercase
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

@ambassador_bp.route('/ambassadors/join', methods=['GET', 'POST'])
def join():
    """Handles the Ambassador Application form loading and submission."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        college = request.form.get('college', '').strip()
        payment_info = request.form.get('payment_info', '').strip()
        
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
            errors.append("Please provide valid payment info (e.g., UPI ID or Bank account details).")
            
        # Check duplicate email
        if not errors:
            rows = execute_read("SELECT id FROM ambassadors WHERE email = %s", (email,))
            if rows:
                errors.append("An application with this email address has already been submitted.")
                
        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template('ambassadors/join.html', name=name, email=email, phone=phone, college=college, payment_info=payment_info)
            
        # Generate code & save to DB
        try:
            referral_code = generate_unique_code(name)
            query = """
            INSERT INTO ambassadors (name, email, phone, college, payment_info, referral_code, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Approved')
            """
            execute_write(query, (name, email, phone, college, payment_info, referral_code))
            
            # Retrieve ID to redirect
            rows = execute_read("SELECT id FROM ambassadors WHERE email = %s", (email,))
            if rows:
                amb_id = rows[0]['id']
                flash("Congratulations! Your application has been approved. Your Offer Letter is ready.", "success")
                return redirect(url_for('ambassador.welcome', amb_id=amb_id))
            else:
                flash("Something went wrong saving your application. Please try again.", "error")
        except Exception as e:
            flash(f"System Error: {e}", "error")
            
    return render_template('ambassadors/join.html')

@ambassador_bp.route('/ambassadors/login', methods=['GET', 'POST'])
def login():
    """Handles passwordless ambassador authentication via email and referral code."""
    if session.get('ambassador_id'):
        return redirect(url_for('ambassador.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        referral_code = request.form.get('referral_code', '').strip()
        
        if not email or not referral_code:
            flash("Please enter both email and referral code.", "error")
            return render_template('ambassadors/login.html', email=email)
            
        rows = execute_read("SELECT id FROM ambassadors WHERE email = %s AND referral_code = %s", (email, referral_code))
        if rows:
            session['ambassador_id'] = rows[0]['id']
            flash("Login successful! Welcome to your Ambassador Dashboard.", "success")
            return redirect(url_for('ambassador.dashboard'))
        else:
            flash("Invalid credentials. Please verify your email and referral code.", "error")
            
    return render_template('ambassadors/login.html')

@ambassador_bp.route('/ambassadors/logout')
def logout():
    """Logs out the ambassador by clearing session credentials."""
    session.pop('ambassador_id', None)
    flash("Session terminated successfully. You have logged out.", "success")
    return redirect(url_for('ambassador.login'))

@ambassador_bp.route('/ambassadors/dashboard')
@ambassador_required
def dashboard():
    """Displays ambassador's personal statistics, account status, and referred clients list."""
    amb_id = session.get('ambassador_id')
    rows = execute_read("SELECT * FROM ambassadors WHERE id = %s", (amb_id,))
    if not rows:
        session.pop('ambassador_id', None)
        return redirect(url_for('ambassador.login'))
        
    ambassador = dict(rows[0])
    
    # Fetch list of inquiries linked to their referral code
    referrals = execute_read(
        "SELECT name, subject, created_at FROM contacts WHERE referral_code = %s ORDER BY created_at DESC",
        (ambassador['referral_code'],)
    )
    
    referrals_count = len(referrals)
    estimated_earnings = referrals_count * 2000 # Estimate ₹2,000 commission per booking on average
    
    # Safely format date in Python
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
        referrals=referrals,
        referrals_count=referrals_count,
        estimated_earnings=estimated_earnings,
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
    
    # Safely format date in Python
    if hasattr(created_at, 'strftime'):
        formatted_date = created_at.strftime('%B %d, %Y')
    else:
        try:
            formatted_date = str(created_at).split()[0]
        except Exception:
            formatted_date = str(created_at)
            
    return render_template('ambassadors/offer_letter.html', ambassador=ambassador, formatted_date=formatted_date)
