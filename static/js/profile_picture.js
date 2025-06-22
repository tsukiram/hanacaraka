// static/js/profile_picture.js
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const messageDiv = document.getElementById('message');
    
    try {
        const response = await fetch('{{ url_for("profile.upload_profile_picture") }}', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRF-Token': '{{ csrf_token() }}'
            }
        });
        const data = await response.json();
        if (response.ok) {
            messageDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            setTimeout(() => {
                window.location.href = '{{ url_for("profile.profile_page") }}';
            }, 2000);
        } else {
            messageDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
    } catch (error) {
        messageDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
});