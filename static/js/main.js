/*
   GlobalTechVibers Core Interactive Script
   Manages client-side validation, Toast Alert popups, and secure AJAX submissions.
*/

document.addEventListener('DOMContentLoaded', () => {
    // 1. Toast Notification Helper
    const showToast = (message, type = 'info') => {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let iconClass = 'bi-info-circle';
        if (type === 'success') iconClass = 'bi-check-circle-fill';
        if (type === 'error') iconClass = 'bi-exclamation-triangle-fill';
        
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="bi ${iconClass}"></i>
                <span>${message}</span>
            </div>
            <button class="toast-close" aria-label="Close alert">&times;</button>
        `;

        container.appendChild(toast);

        // Bind close button event
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            toast.remove();
        });

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse forwards';
            toast.addEventListener('animationend', () => {
                toast.remove();
            });
        }, 5000);
    };

    // Export showToast to global scope in case Jinja template needs to trigger it for flash messages
    window.showToast = showToast;

    // Retrieve CSRF Token from meta tags
    const getCsrfToken = () => {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    };

    // Regex validators
    const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const PHONE_REGEX = /^\+?[0-9\s\-()]{10,20}$/;

    // 2. AJAX Contact Form Submission
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;

            // Fetch field values
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const phone = document.getElementById('phone').value.trim();
            const subject = document.getElementById('subject').value.trim();
            const message = document.getElementById('message').value.trim();

            // Client-side validation checks
            let clientErrors = [];
            if (name.length < 2) clientErrors.push("Name must be at least 2 characters.");
            if (!EMAIL_REGEX.test(email)) clientErrors.push("Please enter a valid email address.");
            if (!PHONE_REGEX.test(phone)) clientErrors.push("Please enter a valid phone number (10-20 digits).");
            if (subject.length < 3) clientErrors.push("Subject must be at least 3 characters.");
            if (message.length < 10) clientErrors.push("Message must be at least 10 characters.");

            if (clientErrors.length > 0) {
                clientErrors.forEach(err => showToast(err, 'error'));
                return;
            }

            // Disable button during network transit
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-arrow-clockwise animate-spin" style="display:inline-block; animation: spin 1s linear infinite;"></i> Sending...';

            try {
                const response = await fetch('/contact/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ name, email, phone, subject, message })
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    showToast(result.message, 'success');
                    contactForm.reset();
                } else {
                    const errorMsgs = result.errors || ["An unexpected error occurred."];
                    errorMsgs.forEach(err => showToast(err, 'error'));
                }
            } catch (err) {
                showToast("Connection to the server failed. Please verify your internet connection.", "error");
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    }

    // 3. AJAX Newsletter Form Submission
    const newsletterForms = document.querySelectorAll('.newsletter-form');
    newsletterForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const emailInput = form.querySelector('input[type="email"]');
            const submitBtn = form.querySelector('button[type="submit"]');
            const email = emailInput.value.trim();

            if (!EMAIL_REGEX.test(email)) {
                showToast("Please enter a valid email address.", "error");
                return;
            }

            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-arrow-clockwise animate-spin" style="display:inline-block; animation: spin 1s linear infinite;"></i>';

            try {
                const response = await fetch('/newsletter/subscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ email })
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    showToast(result.message, 'success');
                    form.reset();
                } else {
                    showToast(result.message || "Failed to subscribe.", 'error');
                }
            } catch (err) {
                showToast("Connection to the server failed.", "error");
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    });
});

// CSS spin animation definition injected dynamically for submission status indicators
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
