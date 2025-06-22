// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\profile.js
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.delete-result-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const resultId = form.dataset.resultId;
            const url = form.dataset.url;
            const csrfToken = form.querySelector('input[name="csrf_token"]').value;

            if (!confirm('Are you sure you want to delete this result?')) {
                return;
            }

            try {
                const formData = new FormData(form);
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRF-Token': csrfToken
                    }
                });

                console.log('Delete response status:', response.status);
                const responseText = await response.text();
                console.log('Delete response text:', responseText.substring(0, 100));

                let data;
                try {
                    data = JSON.parse(responseText);
                } catch (parseError) {
                    console.error('JSON parse error:', parseError);
                    throw new Error('Invalid server response');
                }

                if (response.ok && data.success) {
                    document.getElementById(`result-${resultId}`).remove();
                    const modal = new bootstrap.Modal(document.getElementById('deleteSuccessModal'));
                    modal.show();
                } else {
                    alert(`Error: ${data.error || 'Failed to delete result'}`);
                }
            } catch (error) {
                console.error('Delete error:', error);
                alert(`Error: ${error.message}`);
            }
        });
    });
});