// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\update_profile.js
document.addEventListener('DOMContentLoaded', () => {
    const updateForm = document.getElementById('updateForm');
    const messageDiv = document.getElementById('message');
    const submitButton = updateForm?.querySelector('button[type="submit"]');

    if (!updateForm || !messageDiv) {
        console.error('Update form or message div not found');
        messageDiv.innerHTML = '<div class="alert alert-danger">Error: Page setup is incorrect.</div>';
        return;
    }

    // Store initial values for change detection
    const usernameInput = document.getElementById('username');
    const statusInput = document.getElementById('status');
    const imageInput = document.getElementById('profile_image');
    const initialUsername = usernameInput.value;
    const initialStatus = statusInput.value;

    updateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(updateForm);
        const updateUrl = updateForm.dataset.updateUrl;
        const profilePageUrl = updateForm.dataset.profilePageUrl || '/profile/';
        const csrfToken = updateForm.dataset.csrfToken;

        // Client-side validation
        if (!updateUrl || !csrfToken) {
            messageDiv.innerHTML = '<div class="alert alert-danger">Error: Update configuration is missing.</div>';
            console.error('Missing update URL or CSRF token', { updateUrl, csrfToken });
            return;
        }

        if (usernameInput.value && !/^[a-zA-Z0-9_]{3,80}$/.test(usernameInput.value)) {
            messageDiv.innerHTML = '<div class="alert alert-danger">Username must be 3-80 characters long and contain only letters, numbers, or underscores.</div>';
            usernameInput.focus();
            clearMessageAfterDelay();
            return;
        }

        if (statusInput.value && statusInput.value.length > 200) {
            messageDiv.innerHTML = '<div class="alert alert-danger">Status must be 200 characters or less.</div>';
            statusInput.focus();
            clearMessageAfterDelay();
            return;
        }

        if (imageInput.files.length && !['image/jpeg', 'image/png'].includes(imageInput.files[0].type)) {
            messageDiv.innerHTML = '<div class="alert alert-danger">Only JPG and PNG files are allowed.</div>';
            imageInput.focus();
            clearMessageAfterDelay();
            return;
        }

        // Check if any changes were made
        const hasChanges = (
            usernameInput.value !== initialUsername ||
            statusInput.value !== initialStatus ||
            imageInput.files.length > 0
        );

        if (!hasChanges) {
            messageDiv.innerHTML = '<div class="alert alert-warning">No changes provided.</div>';
            clearMessageAfterDelay();
            return;
        }

        // Disable submit button to prevent multiple submissions
        submitButton.disabled = true;
        submitButton.textContent = 'Updating...';

        try {
            const response = await fetch(updateUrl, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrfToken
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                messageDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                setTimeout(() => {
                    window.location.href = profilePageUrl;
                }, 2000);
            } else {
                messageDiv.innerHTML = `<div class="alert alert-danger">${data.error || 'Failed to update profile'}</div>`;
                console.error('Server error:', data.error);
                clearMessageAfterDelay();
            }
        } catch (error) {
            console.error('Error updating profile:', error);
            messageDiv.innerHTML = '<div class="alert alert-danger">Failed to update profile: Network error</div>';
            clearMessageAfterDelay();
        } finally {
            // Re-enable submit button
            submitButton.disabled = false;
            submitButton.textContent = 'Update Profile';
        }
    });

    // Clear message after 5 seconds
    function clearMessageAfterDelay() {
        setTimeout(() => {
            messageDiv.innerHTML = '';
        }, 5000);
    }
});