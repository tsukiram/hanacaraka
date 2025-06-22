// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\update_profile.js
document.addEventListener('DOMContentLoaded', () => {
    const updateForm = document.getElementById('updateForm');
    const messageDiv = document.getElementById('message');

    if (!updateForm) {
        console.error('Update form not found');
        messageDiv.innerHTML = `<div class="alert alert-danger">Error: Page setup is incorrect.</div>`;
        return;
    }

    updateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(updateForm);
        const updateUrl = updateForm.dataset.updateUrl;
        const csrfToken = updateForm.dataset.csrfToken;
        const usernameInput = document.getElementById('username');
        const imageInput = document.getElementById('profile_image');

        console.log('Update URL:', updateUrl);
        console.log('CSRF Token:', csrfToken);
        console.log('Username provided:', !!usernameInput.value);
        console.log('Image provided:', !!imageInput.files.length);

        if (!updateUrl || !csrfToken) {
            console.error('Missing update URL or CSRF token');
            messageDiv.innerHTML = `<div class="alert alert-danger">Error: Update configuration is missing.</div>`;
            return;
        }

        // Validasi sisi klien
        if (usernameInput.value && !/^[a-zA-Z0-9_]{3,80}$/.test(usernameInput.value)) {
            messageDiv.innerHTML = `<div class="alert alert-danger">Username must be 3-80 characters long and contain only letters, numbers, or underscores.</div>`;
            return;
        }
        if (imageInput.files.length && !['image/jpeg', 'image/png'].includes(imageInput.files[0].type)) {
            messageDiv.innerHTML = `<div class="alert alert-danger">Only JPG and PNG files are allowed.</div>`;
            return;
        }

        try {
            const response = await fetch(updateUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRF-Token': csrfToken
                }
            });

            console.log('Response status:', response.status);
            const responseText = await response.text();
            console.log('Response text:', responseText.substring(0, 100));

            let data;
            try {
                data = JSON.parse(responseText);
            } catch (parseError) {
                console.error('JSON parse error:', parseError);
                throw new Error('Invalid server response');
            }

            if (response.ok) {
                messageDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                setTimeout(() => {
                    window.location.href = updateForm.dataset.profilePageUrl || '/profile/';
                }, 2000);
            } else {
                messageDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            }
        } catch (error) {
            console.error('Update error:', error);
            messageDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        }
    });
});