// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\profile_picture.js
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const messageDiv = document.getElementById('message');

    if (!uploadForm) {
        console.error('Upload form not found');
        messageDiv.innerHTML = `<div class="alert alert-danger">Error: Page setup is incorrect.</div>`;
        return;
    }

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        const uploadUrl = uploadForm.dataset.uploadUrl;
        const csrfToken = uploadForm.dataset.csrfToken;

        console.log('Upload URL:', uploadUrl);
        console.log('CSRF Token:', csrfToken);

        if (!uploadUrl || !csrfToken) {
            console.error('Missing upload URL or CSRF token');
            messageDiv.innerHTML = `<div class="alert alert-danger">Error: Upload configuration is missing.</div>`;
            return;
        }

        try {
            const response = await fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRF-Token': csrfToken
                }
            });

            console.log('Response status:', response.status);
            const responseText = await response.text();
            console.log('Response text:', responseText.substring(0, 100)); // Log 100 karakter pertama

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
                    window.location.href = uploadForm.dataset.profilePageUrl || '/profile/';
                }, 2000);
            } else {
                messageDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            }
        } catch (error) {
            console.error('Upload error:', error);
            messageDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        }
    });
});