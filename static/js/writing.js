// static/js/writing.js
let wordRanges = {};

function initializeWordRanges() {
    try {
        const wordRangesInput = document.getElementById('wordRangesData');
        if (wordRangesInput && wordRangesInput.value) {
            wordRanges = JSON.parse(wordRangesInput.value);
            console.log('Word ranges initialized:', wordRanges);
        } else {
            console.error('wordRangesData not found or empty');
        }
    } catch (error) {
        console.error('Error parsing word ranges:', error);
        const textareas = document.querySelectorAll('.writing-textarea');
        textareas.forEach(textarea => {
            const taskNumber = textarea.dataset.taskNumber;
            const minWords = parseInt(textarea.dataset.minWords);
            const maxWords = parseInt(textarea.dataset.maxWords);
            wordRanges[taskNumber] = { min: minWords, max: maxWords };
        });
        console.log('Word ranges from fallback:', wordRanges);
    }
}

function countWords(text) {
    if (!text || text.trim() === '') return 0;
    const words = text.trim().split(/\s+/).filter(word => word.length > 0);
    return words.length;
}

function updateWordCount(taskNumber, textarea, minWords, maxWords) {
    const words = countWords(textarea.value);
    const wordCountDisplay = document.getElementById(`wordCount_${taskNumber}`);
    
    if (!wordCountDisplay) {
        console.error(`Word count display not found for task ${taskNumber}`);
        return;
    }
    
    wordCountDisplay.textContent = `Word count: ${words}`;
    
    const isValid = words >= minWords && words <= maxWords;
    
    if (isValid) {
        wordCountDisplay.className = 'form-text text-success fw-bold';
        textarea.classList.remove('border-danger', 'border-warning');
        textarea.classList.add('border-success');
    } else if (words > 0) {
        if (words > maxWords) {
            wordCountDisplay.className = 'form-text text-danger fw-bold';
            textarea.classList.remove('border-success', 'border-warning');
            textarea.classList.add('border-danger');
        } else {
            wordCountDisplay.className = 'form-text text-warning fw-bold';
            textarea.classList.remove('border-success', 'border-danger');
            textarea.classList.add('border-warning');
        }
    } else {
        wordCountDisplay.className = 'form-text text-muted';
        textarea.classList.remove('border-success', 'border-warning', 'border-danger');
    }
    
    console.log(`Task ${taskNumber}: ${words} words, valid: ${isValid}, range: ${minWords}-${maxWords}`);
    
    checkAllTasks();
}

function checkAllTasks() {
    const submitButton = document.getElementById('submitButton');
    if (!submitButton) {
        console.error('Submit button not found');
        return;
    }
    
    let allValid = true;
    const textareas = document.querySelectorAll('.writing-textarea');
    
    console.log(`Checking ${textareas.length} textareas`);
    
    textareas.forEach(textarea => {
        const taskNumber = textarea.dataset.taskNumber;
        const minWords = parseInt(textarea.dataset.minWords);
        const maxWords = parseInt(textarea.dataset.maxWords);
        
        if (!taskNumber || isNaN(minWords) || isNaN(maxWords)) {
            console.error(`Invalid data attributes for textarea:`, textarea);
            allValid = false;
            return;
        }
        
        const words = countWords(textarea.value);
        const isValid = words >= minWords && words <= maxWords;
        
        if (!isValid) {
            allValid = false;
        }
        
        console.log(`Task ${taskNumber}: ${words} words, valid: ${isValid}, range: ${minWords}-${maxWords}`);
    });
    
    submitButton.disabled = !allValid;
    
    if (allValid) {
        submitButton.classList.remove('btn-secondary');
        submitButton.classList.add('btn-primary');
    } else {
        submitButton.classList.remove('btn-primary');
        submitButton.classList.add('btn-secondary');
    }
    
    console.log('All tasks valid:', allValid, 'Submit button disabled:', submitButton.disabled);
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    initializeWordRanges();
    
    const textareas = document.querySelectorAll('.writing-textarea');
    textareas.forEach(textarea => {
        const taskNumber = textarea.dataset.taskNumber;
        const minWords = parseInt(textarea.dataset.minWords);
        const maxWords = parseInt(textarea.dataset.maxWords);
        
        textarea.addEventListener('input', function() {
            updateWordCount(taskNumber, this, minWords, maxWords);
        });
        
        updateWordCount(taskNumber, textarea, minWords, maxWords);
    });
    
    console.log('Initialization complete');
});

document.getElementById('writingForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    console.log('Form submission started');
    
    const form = this;
    const submitUrl = form.dataset.submitUrl; // Ambil URL submit
    const resultsUrl = form.dataset.resultsUrl; // Ambil URL results
    const textareas = document.querySelectorAll('.writing-textarea');
    let allValid = true;
    let validationMessages = [];
    
    textareas.forEach(textarea => {
        const taskNumber = textarea.dataset.taskNumber;
        const minWords = parseInt(textarea.dataset.minWords);
        const maxWords = parseInt(textarea.dataset.maxWords);
        const words = countWords(textarea.value);
        
        if (words < minWords) {
            allValid = false;
            validationMessages.push(`Task ${taskNumber}: Need at least ${minWords} words (current: ${words})`);
        } else if (words > maxWords) {
            allValid = false;
            validationMessages.push(`Task ${taskNumber}: Maximum ${maxWords} words allowed (current: ${words})`);
        }
    });
    
    if (!allValid) {
        alert('Please fix the following issues:\n\n' + validationMessages.join('\n'));
        return;
    }
    
    const submitButton = document.getElementById('submitButton');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Submitting...';
    submitButton.disabled = true;
    
    try {
        const formData = new FormData(form);
        console.log('Submitting form data to:', submitUrl);
        
        const response = await fetch(submitUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrf_token') // Tambahkan header CSRF
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        let alertMessage = 'Your Writing Test Results:\n\n';
        data.scores.forEach((score, index) => {
            alertMessage += `Task ${index + 1}:\n`;
            alertMessage += `  • Task Achievement: ${score.task_achievement}/9\n`;
            alertMessage += `  • Coherence & Cohesion: ${score.coherence}/9\n`;
            alertMessage += `  • Vocabulary: ${score.vocabulary}/9\n`;
            alertMessage += `  • Grammar: ${score.grammar}/9\n`;
            alertMessage += `  • Task Score: ${score.overall.toFixed(1)}/9\n\n`;
        });
        alertMessage += `Overall Test Score: ${data.overall_score.toFixed(2)}/9`;
        
        alert(alertMessage);
        window.location.href = resultsUrl;
        
    } catch (error) {
        console.error('Submission error:', error);
        alert('Error submitting test: ' + error.message);
        
        submitButton.textContent = originalText;
        checkAllTasks();
    }
});