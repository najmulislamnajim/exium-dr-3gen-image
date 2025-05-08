document.addEventListener('DOMContentLoaded', function () {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
            // Show the toast
            setTimeout(() => {
                toast.classList.add('show');
            }, 100); // Small delay to ensure smooth transition

            // Hide the toast after 2 seconds
            setTimeout(() => {
                toast.classList.remove('show');
                // Remove the toast from DOM after fade-out
                setTimeout(() => {
                    toast.remove();
                }, 300); // Match transition duration
            }, 3000); // Display for 2 seconds
        });
    });