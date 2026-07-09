# GlobalTechVibers - Corporate Platform

Official corporate website and technical capstone project delivery portal for **GlobalTechVibers**, engineered as a modular, secure, and production-ready Python Flask application.

---

## 🛠 Tech Stack

* **Backend**: Python 3.x, Flask (Blueprint modular routing), Jinja2 Templates.
* **Database**: PostgreSQL (Neon serverless cloud) with built-in SQLite file-based fallback for local zero-config development.
* **Frontend**: Vanilla HTML5, CSS3, and JavaScript. Loaded with **Inter** Google Font and **Bootstrap Icons** CDN. No external UI frameworks (React, Vue, Tailwind, or Bootstrap components) to maintain maximum page speeds.
* **Hosting**: Configured for Render deployment using Gunicorn.

---

## 📂 Project Structure

```text
d:/globaltechvibers/
├── app.py                # Application entrypoint & factory initialization
├── config.py             # Parses environment configuration variables
├── requirements.txt      # Python dependencies manifest
├── instance/             # Local database file storage directory
│   └── globaltechvibers.db (Auto-created local SQLite database)
├── database/
│   └── db.py             # Parameterized SQL query handlers & driver routers
├── blueprints/
│   ├── main.py           # Standard page routes & blog filters
│   └── contact.py        # Secure API endpoints for form submissions
├── static/
│   ├── css/
│   │   ├── style.css     # Design system base, layout, cards, buttons
│   │   ├── responsive.css# Breakpoints and mobile drawer layout
│   │   └── animations.css# Scroll-reveals and button transforms
│   ├── js/
│   │   ├── main.js       # AJAX forms posting, input validation, alerts
│   │   ├── navbar.js     # Sticky header scrolls & responsive toggles
│   │   └── animations.js # Intersection Observer for scroll triggers
│   ├── robots.txt        # Web crawler scanning permissions
│   └── sitemap.xml       # Dynamic site sitemap
└── templates/            # Jinja2 Layout and Page files
    ├── base.html         # Document shell, SEO meta tags, alert bridges
    ├── index.html        # Primary homepage sections
    ├── about.html        # Mission and execution pillars
    ├── services.html     # Capabilities catalog cards grid
    ├── projects.html     # Projects showcase mockup with filter switches
    ├── blog.html         # Searchable & filterable article list
    ├── careers.html      # "No Open Positions" notice page
    ├── contact.html      # Split column location & security form
    ├── privacy.html      # Security & data storage policies
    ├── terms.html        # IP transfer & academic integrity notice
    ├── 404.html          # Custom Page Not Found
    └── 500.html          # Custom Server Error
```

---

## 🚀 Setup & Execution

### 1. Clone the workspace and configure virtualenv
```bash
# Navigate to project root
cd d:/globaltechvibers

# Initialize virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Configuration (`.env`)
Create a `.env` file in the root directory if deploying to production.
```env
SECRET_KEY=your_production_secret_key
DATABASE_URL=postgresql://user:password@neon-host/dbname?sslmode=require
FLASK_DEBUG=True
```
*Note: If `DATABASE_URL` is omitted, the application automatically initializes a local SQLite database at `instance/globaltechvibers.db`.*

### 4. Run the development server
```bash
python app.py
```
Open `http://127.0.0.1:8080` in your web browser.

---

## 🔒 Security Features Implemented

1. **SQL Injection Shield**: Raw SQL queries are fully parameterized. Placeholders translate between Postgres (`%s`) and SQLite (`?`) depending on the selected driver.
2. **CSRF Protection**: All POST forms (contact submission, newsletter subscription) are protected by `Flask-WTF` validation tokens.
3. **Response Security Headers**: Injects `X-Frame-Options: SAMEORIGIN` (frames protection) and `X-Content-Type-Options: nosniff` on all responses.
4. **Backend Input Validation**: Validates name length, email patterns, phone digits count, and message volume on the server side before writing to database.
