/*
   GlobalTechVibers Navigation Script
   Controls sticky header transformation, responsive mobile navigation, and link highlighting.
*/

document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('.header');
    const mobileToggle = document.querySelector('.mobile-nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    const navLinksItems = document.querySelectorAll('.nav-links a');

    // 1. Sticky Header Transformation on Scroll
    const handleScroll = () => {
        if (window.scrollY > 20) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    };
    
    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Run once at start in case page was reloaded pre-scrolled

    // 2. Mobile Nav Drawer Toggle
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', (e) => {
            const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
            
            navLinks.classList.toggle('active');
            mobileToggle.setAttribute('aria-expanded', !isExpanded);
            
            // Toggle hamburger icon if using bootstrap icon
            const icon = mobileToggle.querySelector('i');
            if (icon) {
                if (navLinks.classList.contains('active')) {
                    icon.className = 'bi bi-x';
                } else {
                    icon.className = 'bi bi-list';
                }
            }
            e.stopPropagation();
        });

        // Close menu when clicking outside of it
        document.addEventListener('click', (event) => {
            if (navLinks.classList.contains('active') && !navLinks.contains(event.target) && !mobileToggle.contains(event.target)) {
                navLinks.classList.remove('active');
                mobileToggle.setAttribute('aria-expanded', 'false');
                const icon = mobileToggle.querySelector('i');
                if (icon) icon.className = 'bi bi-list';
            }
        });

        // Close menu on pressing Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                mobileToggle.setAttribute('aria-expanded', 'false');
                const icon = mobileToggle.querySelector('i');
                if (icon) icon.className = 'bi bi-list';
                mobileToggle.focus();
            }
        });
    }

    // 3. Dynamic Active Navigation Link Highlighting
    const currentPath = window.location.pathname;
    let linkMatched = false;

    navLinksItems.forEach(link => {
        const hrefAttr = link.getAttribute('href');
        // Extract relative or absolute path to match
        if (hrefAttr) {
            // Check if current path matches href
            if (currentPath === hrefAttr || (currentPath === '/' && hrefAttr === '/')) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
                linkMatched = true;
            } else if (hrefAttr !== '/' && currentPath.startsWith(hrefAttr)) {
                // For sub-pages matching the prefix (e.g. /blog/article matching /blog)
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
                linkMatched = true;
            }
        }
    });

    // Default fallback to home if nothing else matched
    if (!linkMatched && navLinksItems.length > 0 && currentPath === '/') {
        navLinksItems[0].classList.add('active');
    }
});
