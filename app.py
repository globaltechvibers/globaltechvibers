import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from config import Config
from database.db import init_db

# Instantiate CSRF protection globally
csrf = CSRFProtect()

def create_app():
    """Application factory for creating and configuring the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable global CSRF security
    csrf.init_app(app)
    
    # Initialize connection pools and database schema
    init_db(app)
    
    # Register blueprints (Main routes, form/contact API endpoints, and admin panel)
    from blueprints.main import main_bp
    from blueprints.contact import contact_bp
    from blueprints.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(admin_bp)
    
    # Standard security headers injection
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    # Global Error Page Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 Error: Page not found - {error}")
        return render_template('404.html'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 Error: Server malfunction - {error}")
        return render_template('500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    # Support Render port injection. Bind to 0.0.0.0 if PORT is defined (production), 
    # otherwise fall back to localhost (127.0.0.1) and port 8080 to avoid Windows socket conflicts.
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0' if 'PORT' in os.environ else '127.0.0.1'
    
    app.run(host=host, port=port, debug=app.config.get('DEBUG', False))
