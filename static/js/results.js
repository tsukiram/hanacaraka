// static/js/results.js
document.querySelectorAll('.delete-result-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const resultId = form.dataset.resultId;
        const url = form.dataset.url;
        const formData = new FormData(form);

        if (!confirm('Are you sure you want to delete this result?')) {
            return;
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();

            if (response.ok && data.success) {
                document.getElementById(`result-${resultId}`).remove();
                const modal = new bootstrap.Modal(document.getElementById('deleteSuccessModal'));
                modal.show();
            } else {
                alert(`Error: ${data.error || 'Failed to delete result'}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });
});