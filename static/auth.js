document.addEventListener('DOMContentLoaded', () => {
    console.log('Auth script loaded');

    // Handle logout links
    const logoutLinks = document.querySelectorAll('[data-logout-link]');
    logoutLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            // standard redirect to /logout is fine for cookie-based JWT
        });
    });

    // Check for flash messages in URL or injected by Flask
    // (If using AJAX, we would handle tokens here)
});
