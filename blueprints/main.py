from flask import Blueprint, render_template, request, send_from_directory, current_app
from database.db import execute_read

main_bp = Blueprint('main', __name__)

# Mock database of articles for the Blog page to show dynamic Flask routing
BLOG_ARTICLES = [
    {
        'id': 1,
        'title': "Empowering Academic Success: The Value of Clean Code in Capstone Projects",
        'category': "Academic Support",
        'date': "July 7, 2026",
        'read_time': "5 min read",
        'excerpt': "Final year and IEEE projects serve as a vital bridge between theory and industry. Here is how to apply clean architecture and design patterns to stand out.",
        'image': "blog_academic.jpg",
        'featured': True,
        'content': "Creating robust mini, major, or IEEE capstone projects requires more than just making the code 'work'. It is about applying structured architecture, version control, security checks, and database isolation. In this article, we outline best practices in documentation, test-driven validation, and professional deployment templates that ensure students can showcase enterprise-level engineering during job interviews."
    },
    {
        'id': 2,
        'title': "Architecting Scalable Web Applications with Flask and Neon PostgreSQL",
        'category': "Web Development",
        'date': "July 3, 2026",
        'read_time': "8 min read",
        'excerpt': "Explore blueprint design, connection pooling, and configuration strategies for deploying production-grade python web solutions.",
        'image': "blog_flask.jpg",
        'featured': False,
        'content': "Python Flask is an exceptionally flexible framework. When combined with serverless PostgreSQL (like Neon), it enables rapid feature delivery. The secret lies in splitting the codebase using Flask Blueprints, preventing connection bloat using thread-safe connection pooling, escaping raw parameters to thwart SQL injections, and setting up strict security response headers. We walk through a boilerplate setup ready to deploy."
    },
    {
        'id': 3,
        'title': "The Role of AI and LLM APIs in Automating Business Workflows",
        'category': "Artificial Intelligence",
        'date': "June 25, 2026",
        'read_time': "6 min read",
        'excerpt': "How companies use OpenAI and Google Gemini APIs to optimize support, parse documents, and build smart agents.",
        'image': "blog_ai.jpg",
        'featured': False,
        'content': "Integrating AI into business workflow solutions is no longer a luxury. Modern automation utilities leverage pre-trained LLMs to categorize emails, answer common queries, draft standard documents, and summarize technical reports. Learn how to architect clean RESTful endpoints around OpenAI and Gemini API systems, implement token count limits, and cache responses to keep operating costs low."
    },
    {
        'id': 4,
        'title': "Database Normalization and Index Optimization: A Practical Guide",
        'category': "Database Solutions",
        'date': "June 18, 2026",
        'read_time': "7 min read",
        'excerpt': "Learn how poor schema definitions slow down CRM databases and how normalization and indexing resolve bottlenecks.",
        'image': "blog_db.jpg",
        'featured': False,
        'content': "Database bottlenecks are one of the most common causes of slow web applications. By understanding proper primary/foreign keys, third normal form (3NF), and adding indices on columns frequently used in WHERE and JOIN statements, page load times can drop from seconds to milliseconds. We compare index structures and discuss transaction isolation levels."
    }
]

@main_bp.route('/')
def index():
    # Show the featured article and a subset of services on home page
    featured_blog = next((a for a in BLOG_ARTICLES if a['featured']), None)
    return render_template('index.html', featured_blog=featured_blog)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/services')
def services():
    return render_template('services.html')

@main_bp.route('/projects')
def projects():
    return render_template('projects.html')

@main_bp.route('/blog')
def blog():
    category_filter = request.args.get('category', '').strip()
    search_query = request.args.get('q', '').strip().lower()
    
    filtered_articles = BLOG_ARTICLES
    
    # Apply category filter
    if category_filter:
        filtered_articles = [a for a in filtered_articles if a['category'].lower() == category_filter.lower()]
        
    # Apply search filter
    if search_query:
        filtered_articles = [
            a for a in filtered_articles 
            if search_query in a['title'].lower() or search_query in a['excerpt'].lower() or search_query in a['category'].lower()
        ]
        
    # Get distinct categories for filter buttons
    categories = sorted(list(set(a['category'] for a in BLOG_ARTICLES)))
    
    # Separate featured article if not filtering or searching
    featured_article = None
    if not category_filter and not search_query:
        featured_article = next((a for a in BLOG_ARTICLES if a['featured']), None)
        # Exclude featured article from the main list in grid
        display_articles = [a for a in filtered_articles if not a['featured']]
    else:
        display_articles = filtered_articles
        
    return render_template(
        'blog.html',
        articles=display_articles,
        featured=featured_article,
        categories=categories,
        selected_category=category_filter,
        search_query=request.args.get('q', '')
    )

@main_bp.route('/careers')
def careers():
    try:
        jobs = execute_read("SELECT * FROM jobs ORDER BY created_at DESC")
    except Exception as e:
        current_app.logger.error(f"Careers DB Error: {e}")
        jobs = []
    return render_template('careers.html', jobs=jobs)

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/robots.txt')
def robots():
    return send_from_directory(current_app.static_folder, 'robots.txt')

@main_bp.route('/sitemap.xml')
def sitemap():
    return send_from_directory(current_app.static_folder, 'sitemap.xml')
