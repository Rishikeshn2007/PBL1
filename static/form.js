document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('healthForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            // Optional: form validation or AJAX submission
            console.log('Form submitting...');
        });
    }
});
