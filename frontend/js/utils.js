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
    if (!dateString) return '';

    // Ensure the datetime string is treated as UTC
    // If it doesn't end with 'Z' and doesn't have a timezone offset, add 'Z'
    let utcString = dateString;
    if (!dateString.endsWith('Z') && !dateString.match(/[+-]\d{2}:\d{2}$/)) {
        utcString = dateString + 'Z';
    }

    // Parse as UTC and convert to local timezone
    const date = new Date(utcString);

    // Format in MM/DD/YYYY HH:mm AM/PM format
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };

    return date.toLocaleString('en-US', options);
}

function copyToClipboard(text) {
    // Try modern Clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showSuccess('Copied to clipboard!');
        }).catch(() => {
            showError('Failed to copy to clipboard');
        });
    } else {
        // Fallback to older method
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showSuccess('Copied to clipboard!');
        } catch (err) {
            showError('Failed to copy to clipboard');
        }
        document.body.removeChild(textarea);
    }
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
