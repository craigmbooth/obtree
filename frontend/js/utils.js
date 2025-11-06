// Utility functions
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        setTimeout(() => {
            errorDiv.classList.add('hidden');
        }, 5000);
    } else {
        alert(message);
    }
}

function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.classList.remove('hidden');
        setTimeout(() => {
            successDiv.classList.add('hidden');
        }, 5000);
    } else {
        alert(message);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showSuccess('Copied to clipboard!');
    }).catch(() => {
        showError('Failed to copy to clipboard');
    });
}

function updateNavigation() {
    const user = Auth.getUser();
    const userEmailSpan = document.getElementById('user-email');
    const siteAdminLink = document.getElementById('site-admin-link');

    if (userEmailSpan && user) {
        userEmailSpan.textContent = user.email;
    }

    if (siteAdminLink && user && user.is_site_admin) {
        siteAdminLink.classList.remove('hidden');
    }
}
