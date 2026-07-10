/*
   GlobalTechVibers Navigation Script
   Controls sticky header transformation, responsive mobile navigation, and link highlighting.
*/

document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('.header');
    const mobileToggle = document.querySelector('.mobile-nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    const navLinksItems = document.querySelectorAll('.nav-links a, .nav-pill-links a');
    const body = document.body;

    const setNavOpen = (isOpen) => {
        navLinks.classList.toggle('active', isOpen);
        mobileToggle.setAttribute('aria-expanded', String(isOpen));
        body.classList.toggle('nav-open', isOpen);

        const icon = mobileToggle.querySelector('i');
        if (icon) {
            icon.className = isOpen ? 'bi bi-x' : 'bi bi-list';
        }
    };

    // 1. Sticky Header Transformation on Scroll
    const handleScroll = () => {
        const isDarkHeroPage = document.querySelector('.hero-section-video') !== null || document.querySelector('.research-bg-video-container') !== null;
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
            if (isDarkHeroPage) {
                header.classList.remove('header-dark-glass');
            }
        } else {
            header.classList.remove('scrolled');
            if (isDarkHeroPage) {
                header.classList.add('header-dark-glass');
            }
        }
    };
    
    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Run once at start in case page was reloaded pre-scrolled

    // 2. Mobile Nav Drawer Toggle
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', (e) => {
            const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
            setNavOpen(!isExpanded);
            e.stopPropagation();
        });

        navLinksItems.forEach((link) => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 992) {
                    setNavOpen(false);
                }
            });
        });

        document.addEventListener('click', (event) => {
            if (navLinks.classList.contains('active') && !navLinks.contains(event.target) && !mobileToggle.contains(event.target)) {
                setNavOpen(false);
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && navLinks.classList.contains('active')) {
                setNavOpen(false);
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
