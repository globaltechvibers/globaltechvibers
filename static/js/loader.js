/*
   GlobalTechVibers - Premium Intro Loader Script
   Controls the timing sequence, sessionStorage locks, accessibility checks, and entrance animations.
*/

document.addEventListener('DOMContentLoaded', () => {
    // 1. Check for reduced motion and previous loads in the current browser session
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const hasLoadedBefore = sessionStorage.getItem('gtv_has_loaded_before');
    
    const loader = document.getElementById('intro-loader');
    const homepage = document.getElementById('homepage-content');
    
    if (prefersReducedMotion || hasLoadedBefore) {
        // Accessibility / Performance bypass: Skip loader completely
        if (loader) {
            loader.style.display = 'none';
        }
        if (homepage) {
            homepage.classList.remove('homepage-content-hidden');
            homepage.classList.add('homepage-content-visible-instant');
        }
        document.body.classList.remove('loading-active');
        return;
    }
    
    // 2. Lock scrolls and prep animations
    document.body.classList.add('loading-active');
    
    const textSteps = [
        { id: 'step-1', duration: 1600 }, // Building Tomorrow
        { id: 'step-2', duration: 1600 }, // Engineering Innovation
        { id: 'step-3', duration: 2000 }, // Web Apps, AI, Projects
        { id: 'step-4', duration: 1800 }  // Empowering Student Innovation
    ];
    
    let currentDelay = 0;
    
    // 3. Sequential Animation Schedule for Text
    textSteps.forEach((step, index) => {
        // Fade In text (make active)
        setTimeout(() => {
            const el = document.getElementById(step.id);
            if (el) el.classList.add('active');
        }, currentDelay);
        
        // Fade Out text (slide up and disappear 400ms before step duration completes)
        setTimeout(() => {
            const el = document.getElementById(step.id);
            if (el) el.classList.add('exit');
        }, currentDelay + step.duration - 400);
        
        currentDelay += step.duration;
    });
    
    // 4. Logo Reveal Step (lasts 800ms)
    setTimeout(() => {
        const logoStep = document.getElementById('step-logo');
        if (logoStep) {
            logoStep.classList.add('active');
        }
    }, currentDelay);
    
    // 5. Loader Exit & Homepage Entrance trigger (800ms after logo starts)
    setTimeout(() => {
        // Loader fades away
        if (loader) {
            loader.classList.add('fade-out');
        }
        
        // Homepage reveals
        if (homepage) {
            homepage.classList.remove('homepage-content-hidden');
            homepage.classList.add('homepage-content-visible');
        }
        
        // Trigger page elements slide-ups
        triggerHomepageEntrance();
    }, currentDelay + 800);
    
    // 6. Final cleanup (complete fade-out transition duration of 800ms)
    setTimeout(() => {
        if (loader) {
            loader.style.display = 'none';
        }
        document.body.classList.remove('loading-active');
        
        // Mark session lock so user isn't slowed down on subsequent navigations back home
        sessionStorage.setItem('gtv_has_loaded_before', 'true');
    }, currentDelay + 800 + 800);

    // 7. Staggered Homepage Entry Animations
    function triggerHomepageEntrance() {
        // Prepare initial hidden positions
        document.body.classList.add('entrance-ready');
        if (homepage) homepage.classList.add('entrance-ready');
        
        // Force layout reflow to register styles
        document.body.offsetHeight;
        
        // Trigger active slide-ups
        document.body.classList.add('entrance-active');
        if (homepage) homepage.classList.add('entrance-active');
        
        if (homepage) {
            // Staggered delay for service/project cards (80ms spacing)
            const cards = homepage.querySelectorAll('.card');
            cards.forEach((card, idx) => {
                card.style.transitionDelay = `${idx * 80}ms`;
            });
            
            // Subtle transition delay for buttons in hero
            const buttons = homepage.querySelectorAll('.hero-buttons .btn');
            buttons.forEach(btn => {
                btn.style.transitionDelay = '200ms';
            });
        }
    }
});
