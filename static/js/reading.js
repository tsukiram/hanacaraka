// static/js/reading.js
document.getElementById('readingForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const form = this;
    const submitUrl = form.dataset.submitUrl; // Ambil URL submit
    const resultsUrl = form.dataset.resultsUrl; // Ambil URL results
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;

    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';

    try {
        const response = await fetch(submitUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrf_token')
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }

        alert(`Your score: ${data.score.percentage.toFixed(2)}% (${data.score.correct}/${data.score.total})`);
        window.location.href = resultsUrl; // Gunakan resultsUrl
    } catch (error) {
        console.error('Submission error:', error);
        alert('Error submitting test: ' + error.message);
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
    }
});