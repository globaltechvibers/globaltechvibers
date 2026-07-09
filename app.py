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
        
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"403 Error: Access Forbidden - {error}")
        return render_template('403.html'), 403
        
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 Error: Server malfunction - {error}")
        return render_template('500.html'), 500

    return app

app = create_app()

def is_port_available(host, port):
    """Checks if a port is available for binding on the specified host."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False

if __name__ == '__main__':
    # Support Render port injection. Bind to 0.0.0.0 if PORT is defined (production), 
    # otherwise fall back to localhost (127.0.0.1) and scan candidate ports to avoid Windows socket conflicts.
    host = '0.0.0.0' if 'PORT' in os.environ else '127.0.0.1'
    
    if 'PORT' in os.environ:
        # Production (Render) - strict port binding
        port = int(os.environ['PORT'])
        app.run(host=host, port=port, debug=app.config.get('DEBUG', False))
    else:
        # Local development - try sequential ports if 8080 is restricted or in use
        candidate_ports = [8080, 8081, 8082, 8083, 8084, 8085, 9090, 5000, 5001]
        server_started = False
        
        for p in candidate_ports:
            if not is_port_available(host, p):
                print(f"[PORT CONFLICT] Port {p} is restricted or already in use.")
                print("[*] Automatically shifting to next fallback candidate port...")
                continue
                
            try:
                # Run Werkzeug server
                app.run(host=host, port=p, debug=app.config.get('DEBUG', False))
                server_started = True
                break
            except (OSError, SystemExit) as e:
                print(f"[PORT CONFLICT] Port {p} failed to run: {e}")
                print("[*] Automatically shifting to next fallback candidate port...")
                
        if not server_started:
            print("[CRITICAL ERROR] All local fallback candidate ports are blocked. Please inspect socket permissions.")
