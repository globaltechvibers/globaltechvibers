/*
   GlobalTechVibers Viewport Animation Trigger
   Leverages IntersectionObserver to animate content columns when scrolled into view.
*/

document.addEventListener('DOMContentLoaded', () => {
    // Select all elements prepared for scroll reveal animations
    const revealElements = document.querySelectorAll('.reveal');

    if ('IntersectionObserver' in window) {
        // Configure observer options
        const observerOptions = {
            root: null, // relative to the viewport
            rootMargin: '0px 0px -60px 0px', // trigger slightly before entering viewport
            threshold: 0.15 // trigger when 15% of the element is visible
        };

        const revealCallback = (entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Add active class to start CSS animation
                    entry.target.classList.add('active');
                    // Once animated, we no longer need to observe it
                    observer.unobserve(entry.target);
                }
            });
        };

        const observer = new IntersectionObserver(revealCallback, observerOptions);

        revealElements.forEach(element => {
            observer.observe(element);
        });
    } else {
        // Fallback for older browsers: show all elements instantly
        revealElements.forEach(element => {
            element.classList.add('active');
        });
    }

    // Failsafe: force reveal all elements after 1.2 seconds in case IntersectionObserver is delayed or blocked
    setTimeout(() => {
        revealElements.forEach(element => {
            if (!element.classList.contains('active')) {
                element.classList.add('active');
            }
        });
    }, 1200);
});
