import os
import logging
from twilio.rest import Client

# Configure logger
logger = logging.getLogger(__name__)

def send_whatsapp_booking_alerts(student_name, student_phone, project_title, price_formatted, referral_code=None):
    """Sends automated WhatsApp notifications to both the site administrator and the student."""
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
    admin_number = os.environ.get('ADMIN_WHATSAPP_NUMBER', 'whatsapp:+918328186045')

    if not account_sid or not auth_token:
        logger.warning(
            "WhatsApp Alert: Twilio credentials not configured in environment (TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN is missing). "
            f"Alert skipped. Details: Student={student_name}, Phone={student_phone}, Project={project_title}."
        )
        return False

    try:
        client = Client(account_sid, auth_token)

        # 1. Format numbers
        # Remove spaces, dashes, parentheses and prefix country code if not present
        def clean_number(num):
            cleaned = "".join([c for c in num if c.isdigit()])
            if not cleaned.startswith('91') and len(cleaned) == 10:
                cleaned = '91' + cleaned
            return f"whatsapp:+{cleaned}"

        target_student_number = clean_number(student_phone)

        # 2. Dispatch message to the Admin
        admin_body = (
            f"🔔 *New Live Demo Booking!*\n\n"
            f"👤 *Student Name:* {student_name}\n"
            f"📱 *WhatsApp Number:* {student_phone}\n"
            f"📚 *Selected Project:* {project_title}\n"
            f"💰 *Project Price:* {price_formatted}\n"
            f"🔑 *Referral Code:* {referral_code or 'None'}\n\n"
            f"👉 *Action:* Message the student on WhatsApp immediately to coordinate their live video demonstration schedule!"
        )
        
        client.messages.create(
            body=admin_body,
            from_=from_number,
            to=admin_number
        )
        logger.info(f"WhatsApp Alert sent to Admin for booking by {student_name}.")

        # 3. Dispatch message to the Student
        student_body = (
            f"Hi {student_name}! 🚀 Thank you for booking a free live demo for *{project_title}* on GlobalTechVibers.\n\n"
            f"A senior developer will message you on this WhatsApp number shortly to coordinate a live video execution demonstration via Google Meet/AnyDesk.\n\n"
            f"💬 *Want to start the demo right now?* Message our team coordinator directly: https://wa.me/918328186045"
        )

        client.messages.create(
            body=student_body,
            from_=from_number,
            to=target_student_number
        )
        logger.info(f"WhatsApp Confirmation sent to Student {student_name} ({student_phone}).")
        return True

    except Exception as e:
        logger.error(f"Failed to dispatch WhatsApp booking notifications: {e}")
        return False
