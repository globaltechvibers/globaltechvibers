import os
import sqlite3
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# Global connection configuration
_db_type = None  # 'postgres' or 'sqlite'
_pg_pool = None
_sqlite_path = None

def init_db(app):
    """Initializes the database connection pool or SQLite fallback and creates tables."""
    global _db_type, _pg_pool, _sqlite_path
    
    db_url = app.config.get('DATABASE_URL')
    
    if db_url and (db_url.startswith('postgres://') or db_url.startswith('postgresql://')):
        # Fix Neon's old default URL scheme if needed
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        _db_type = 'postgres'
        app.logger.info("Database: Configuring PostgreSQL (Neon) connection pool.")
        try:
            # We initialize a simple connection pool with min 1, max 10 connections
            _pg_pool = SimpleConnectionPool(1, 10, dsn=db_url)
            # Test a connection
            conn = _pg_pool.getconn()
            _pg_pool.putconn(conn)
            app.logger.info("Database: PostgreSQL connected successfully.")
        except Exception as e:
            app.logger.error(f"Database: Failed to establish PostgreSQL connection: {e}")
            raise e
    else:
        _db_type = 'sqlite'
        # Fallback to local SQLite in instance folder
        instance_dir = app.instance_path
        os.makedirs(instance_dir, exist_ok=True)
        _sqlite_path = os.path.join(instance_dir, 'globaltechvibers.db')
        app.logger.info(f"Database: Falling back to SQLite at: {_sqlite_path}")
    
    # Create required tables
    _create_tables(app)

def get_connection():
    """Retrieves a database connection based on the active driver."""
    if _db_type == 'postgres':
        if not _pg_pool:
            raise RuntimeError("PostgreSQL Connection Pool is not initialized.")
        return _pg_pool.getconn()
    else:
        conn = sqlite3.connect(_sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

def release_connection(conn):
    """Releases a connection back to the pool or closes the SQLite file."""
    if _db_type == 'postgres':
        if _pg_pool and conn:
            _pg_pool.putconn(conn)
    else:
        if conn:
            conn.close()

def _create_tables(app):
    """Helper method to run DDL scripts for table initialization."""
    if _db_type == 'postgres':
        contacts_sql = """
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            subject VARCHAR(150) NOT NULL,
            message TEXT NOT NULL,
            referral_code VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        newsletter_sql = """
        CREATE TABLE IF NOT EXISTS newsletter (
            id SERIAL PRIMARY KEY,
            email VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        jobs_sql = """
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            department VARCHAR(100) NOT NULL,
            location VARCHAR(100) NOT NULL,
            type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        applications_sql = """
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            job_id INT NOT NULL,
            job_title VARCHAR(150) NOT NULL,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            resume_path VARCHAR(255) NOT NULL,
            cover_letter TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        ambassadors_sql = """
        CREATE TABLE IF NOT EXISTS ambassadors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            phone VARCHAR(20) NOT NULL,
            college VARCHAR(150) NOT NULL,
            payment_info VARCHAR(255) NOT NULL,
            referral_code VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255),
            status VARCHAR(50) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        projects_sql = """
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            technologies VARCHAR(255) NOT NULL,
            price INTEGER NOT NULL,
            status VARCHAR(50) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        bookings_sql = """
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            project_title VARCHAR(255) NOT NULL,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            referral_code VARCHAR(50),
            status VARCHAR(50) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        custom_requests_sql = """
        CREATE TABLE IF NOT EXISTS custom_requests (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            department VARCHAR(50) NOT NULL,
            topic VARCHAR(200) NOT NULL,
            requirements TEXT NOT NULL,
            deadline VARCHAR(50),
            status VARCHAR(50) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    else:
        contacts_sql = """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            referral_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        newsletter_sql = """
        CREATE TABLE IF NOT EXISTS newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        jobs_sql = """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            location TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        applications_sql = """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            resume_path TEXT NOT NULL,
            cover_letter TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        ambassadors_sql = """
        CREATE TABLE IF NOT EXISTS ambassadors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            college TEXT NOT NULL,
            payment_info TEXT NOT NULL,
            referral_code TEXT NOT NULL UNIQUE,
            password_hash TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        projects_sql = """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            technologies TEXT NOT NULL,
            price INTEGER NOT NULL,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        bookings_sql = """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            project_title TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            referral_code TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        custom_requests_sql = """
        CREATE TABLE IF NOT EXISTS custom_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            department TEXT NOT NULL,
            topic TEXT NOT NULL,
            requirements TEXT NOT NULL,
            deadline TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(contacts_sql)
        cur.execute(newsletter_sql)
        cur.execute(jobs_sql)
        cur.execute(applications_sql)
        cur.execute(ambassadors_sql)
        cur.execute(projects_sql)
        cur.execute(bookings_sql)
        cur.execute(custom_requests_sql)
        conn.commit()
        
        # Seed default Campus Tech Ambassador job if empty
        cur.execute("SELECT COUNT(*) FROM jobs;")
        count = cur.fetchone()[0]
        if count == 0:
            placeholder = '?' if _db_type == 'sqlite' else '%s'
            seed_query = f"""
            INSERT INTO jobs (title, department, location, type, description, requirements)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """
            cur.execute(seed_query, (
                'Campus Tech Ambassador',
                'Marketing & Sales',
                'Remote / On-Campus',
                'Internship',
                'Represent GlobalTechVibers on your campus. Share final-year capstone and college project catalogs in student WhatsApp groups, department forums, and coding clubs to earn performance-based commissions.',
                'Enrolled in an Engineering / Computer Science / IT degree program\nStrong communication and networking skills\nActive in student groups or clubs'
            ))
            cur.execute(seed_query, (
                'Business Development Intern (Unpaid / Commission-Based)',
                'Business Development',
                'Remote / Part-Time (10-15 hours/week)',
                'Internship',
                'Work directly with the Founder to learn B2B tech sales and client acquisition. Conduct market research on Discord, Telegram, and LinkedIn to find prospective clients, draft personalized outreach messages for small businesses and academic groups, and manage our lead pipeline in our CRM. Earn a high commission % cut of every web/software project you help close, direct 1-on-1 mentorship from the founder, and an official certificate of completion with a strong LinkedIn recommendation.',
                'Student or recent graduate in Business, Marketing, or Computer Science\nBasic understanding of tech terms (Web apps, AI, Databases)\nExcellent written communication skills in English'
            ))
            conn.commit()
            app.logger.info("Database: Seeded default jobs (Campus Ambassador & BD Intern).")

        # Seed default projects if they don't exist
        placeholder = '?' if _db_type == 'sqlite' else '%s'
        seed_proj_query = f"""
        INSERT INTO projects (title, category, description, technologies, price)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """
        projects_data = [
            (
                'Autonomous AI Research Agent',
                'ai-ml',
                'An autonomous research assistant that takes any topic, fetches top web sources via DuckDuckGo, synthesizes findings using Groq LLaMA models, and exports citation-backed research briefs.',
                'Flask, Python, Groq API, DuckDuckGo Search',
                7999
            ),
            (
                'Aegis RAG: Document Q&A System',
                'ai-ml',
                'An advanced Retrieval-Augmented Generation (RAG) system utilizing FastAPI and local FAISS vector indices to query custom PDF documents with real-time semantic context injection.',
                'FastAPI, Python, FAISS Vector DB, Gemini API',
                9999
            ),
            (
                'StegoShare: Secure Image Steganography System',
                'cybersecurity',
                'An advanced image steganography platform leveraging FastAPI and LSB pixel encoding to hide AES-256 encrypted messages inside standard images without visual degradation.',
                'FastAPI, Python, Cryptography (AES-256), Pillow',
                7999
            ),
            (
                'TrustChain: Cryptographic E-Voting Ledger',
                'blockchain',
                'A secure, transparent digital voting platform using cryptographic block hashing to form an immutable ledger, preventing database tampering and double-voting.',
                'FastAPI, Python, SHA-256 Hash Chain, SQLite',
                8999
            ),
            (
                'DeepGuard: CNN-Based Plant Disease Classifier',
                'ai-ml',
                'A deep learning convolutional neural network (CNN) system designed to detect and classify crop leaf diseases from uploaded images with statistical confidence readouts.',
                'Python, TensorFlow, OpenCV, Flask',
                8999
            ),
            (
                'CipherVault: Secure File Storage with Hybrid Encryption',
                'cybersecurity',
                'A secure cloud vault featuring hybrid cryptography, encrypting user files locally with symmetric AES keys and locking keys asynchronously with RSA key pairs.',
                'Python, Cryptography (AES + RSA), Flask, SQLite',
                8499
            ),
            (
                'Intellecta: Automated Resume ATS Screener & Matcher',
                'ai-ml',
                'An intelligent resume parsing system utilizing Natural Language Processing (NLP) and cosine similarity metrics to screen CVs against job descriptions and display ATS scores.',
                'Python, Flask, SpaCy NLP, SQLite',
                7499
            ),
            (
                'Sentinel: Real-Time Server Performance & Uptime Monitor',
                'cloud',
                'A lightweight systems monitoring dashboard displaying real-time CPU, RAM, and disk utilization charts with automated SMTP email alert configurations.',
                'FastAPI, Python, Psutil, Chart.js, SQLite',
                6999
            ),
            (
                'Apex Ledger: Business CRM with Invoice PDF Mailer',
                'web-development',
                'A complete client relations management (CRM) platform equipped with sales pipelines, contact management directories, and automated PDF invoice mailing queues.',
                'Python, Flask, SQLite, ReportLab, SMTP',
                7999
            ),
            (
                'MediChain: Patient Electronic Health Records Blockchain Ledger',
                'blockchain',
                'A secure patient electronic health records (EHR) database simulated on a local cryptographic blockchain ledger to enforce medical record compliance and privacy.',
                'Python, Flask, SHA-256 Block Ledger, Cryptography',
                9499
            )
        ]
        
        # Clean up any old demo projects dynamically
        project_titles = [p[0] for p in projects_data]
        placeholders_str = ', '.join([placeholder] * len(project_titles))
        cur.execute(f"DELETE FROM projects WHERE title NOT IN ({placeholders_str});", tuple(project_titles))
        
        for proj in projects_data:
            cur.execute(f"SELECT COUNT(*) FROM projects WHERE title = {placeholder};", (proj[0],))
            exists = cur.fetchone()[0]
            if exists == 0:
                cur.execute(seed_proj_query, proj)
        conn.commit()
        app.logger.info("Database: Seeded default project catalog (only Autonomous AI Research Agent).")
            
        cur.close()
        app.logger.info("Database: Tables initialized or verified successfully.")
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Database: Table creation failed: {e}")
        raise e
    finally:
        release_connection(conn)

    # Database Schema Migration: Check and add referral_code column to contacts table if missing
    try:
        conn = get_connection()
        cur = conn.cursor()
        if _db_type == 'sqlite':
            cur.execute("PRAGMA table_info(contacts);")
            columns = [row[1] for row in cur.fetchall()]
            if 'referral_code' not in columns:
                cur.execute("ALTER TABLE contacts ADD COLUMN referral_code TEXT;")
                conn.commit()
                app.logger.info("Database: Migrated SQLite contacts table adding referral_code.")
        else:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='contacts' AND column_name='referral_code';
            """)
            row = cur.fetchone()
            if not row:
                cur.execute("ALTER TABLE contacts ADD COLUMN referral_code VARCHAR(50);")
                conn.commit()
                app.logger.info("Database: Migrated Postgres contacts table adding referral_code.")
        cur.close()
    except Exception as e:
        app.logger.warning(f"Database Migration Warning (referral_code check): {e}")
    finally:
        release_connection(conn)

    # Database Schema Migration: Check and add password_hash column to ambassadors table if missing
    try:
        conn = get_connection()
        cur = conn.cursor()
        if _db_type == 'sqlite':
            cur.execute("PRAGMA table_info(ambassadors);")
            columns = [row[1] for row in cur.fetchall()]
            if 'password_hash' not in columns:
                cur.execute("ALTER TABLE ambassadors ADD COLUMN password_hash TEXT;")
                conn.commit()
                app.logger.info("Database: Migrated SQLite ambassadors table adding password_hash.")
        else:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='ambassadors' AND column_name='password_hash';
            """)
            row = cur.fetchone()
            if not row:
                cur.execute("ALTER TABLE ambassadors ADD COLUMN password_hash VARCHAR(255);")
                conn.commit()
                app.logger.info("Database: Migrated Postgres ambassadors table adding password_hash.")
        cur.close()
    except Exception as e:
        app.logger.warning(f"Database Migration Warning (password_hash check): {e}")
    finally:
        release_connection(conn)

def execute_write(query, params=None):
    """Executes a parameterized write query (INSERT, UPDATE, DELETE)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if _db_type == 'sqlite':
            # Translate placeholder from %s (Postgres standard) to ? (SQLite standard)
            query = query.replace('%s', '?')
        cur.execute(query, params or ())
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)

def execute_read(query, params=None):
    """Executes a parameterized read query and returns results as lists of dictionaries."""
    conn = get_connection()
    try:
        if _db_type == 'sqlite':
            query = query.replace('%s', '?')
            cur = conn.cursor()
            cur.execute(query, params or ())
            rows = cur.fetchall()
            result = [dict(row) for row in rows]
        else:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params or ())
            rows = cur.fetchall()
            result = [dict(row) for row in rows]
        cur.close()
        return result
    except Exception as e:
        raise e
    finally:
        release_connection(conn)

def get_db_type():
    """Returns the active database driver type ('postgres' or 'sqlite')."""
    return _db_type
