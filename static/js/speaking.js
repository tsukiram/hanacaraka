// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\speaking.js
document.addEventListener('DOMContentLoaded', () => {
    let mediaRecorder = null;
    let audioBlobs = {};
    let transcriptions = {};
    let timerInterval = null;
    let isRecording = false;
    let totalTasks = document.querySelectorAll('.start-recording').length;

    console.log(`Total tasks: ${totalTasks}`);

    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
        const secs = (seconds % 60).toString().padStart(2, '0');
        return `${mins}:${secs}`;
    }

    function startTimer(taskNumber, duration, state, onComplete) {
        const timerElement = document.getElementById(`timer-${taskNumber}`);
        let timeLeft = duration;
        timerElement.textContent = formatTime(timeLeft);
        timerElement.classList.add(`timer-${state}`);
        timerElement.setAttribute('aria-label', `${state === 'preparing' ? 'Preparation' : 'Recording'} time remaining: ${formatTime(timeLeft)}`);

        timerInterval = setInterval(() => {
            timeLeft--;
            timerElement.textContent = formatTime(timeLeft);
            timerElement.setAttribute('aria-label', `${state === 'preparing' ? 'Preparation' : 'Recording'} time remaining: ${formatTime(timeLeft)}`);
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                timerElement.classList.remove(`timer-${state}`);
                onComplete();
            }
        }, 1000);
    }

    function stopTimer(taskNumber) {
        if (timerInterval) {
            clearInterval(timerInterval);
            const timerElement = document.getElementById(`timer-${taskNumber}`);
            timerElement.classList.remove('timer-preparing', 'timer-recording');
            timerElement.textContent = '00:00';
            timerElement.setAttribute('aria-label', 'Timer stopped');
        }
    }

    function checkAllTasksCompleted() {
        const submitAllButton = document.getElementById('submit-all-tasks');
        if (Object.keys(transcriptions).length === totalTasks) {
            submitAllButton.disabled = false;
            console.log('All tasks completed, enabling submit button');
        } else {
            submitAllButton.disabled = true;
        }
    }

    // Pilih container spesifik di dalam speaking test
    const container = document.querySelector('.container[data-transcribe-url]');
    console.log('Speaking container found:', !!container);
    if (!container) {
        console.error('Speaking container element not found');
        alert('Error: Page setup is incorrect. Please refresh the page.');
        return;
    }
    console.log('Transcribe URL:', container.dataset.transcribeUrl);
    console.log('Submit URL:', container.dataset.submitUrl);
    console.log('Results URL:', container.dataset.resultsUrl);

    document.querySelectorAll('.start-recording').forEach(button => {
        button.addEventListener('click', async function() {
            if (isRecording) {
                alert('Another recording is in progress. Please stop it first.');
                return;
            }

            const taskNumber = this.getAttribute('data-task');
            const preparationTime = parseInt(this.getAttribute('data-preparation')) * 1000;
            const responseTime = parseInt(this.getAttribute('data-response')) * 1000;
            const form = document.getElementById(`speakingForm-${taskNumber}`);
            const transcriptionInput = form.querySelector('input[name="transcription"]');
            const timerElement = document.getElementById(`timer-${taskNumber}`);
            const soundwaveElement = document.getElementById(`soundwave-${taskNumber}`);
            const playbackElement = document.getElementById(`playback-${taskNumber}`);
            const stopButton = this.parentElement.querySelector('.stop-recording');
            const audioElement = playbackElement.querySelector('audio');
            const transcriptionElement = document.getElementById(`transcription-${taskNumber}`);
            const transcribeUrl = container.dataset.transcribeUrl;

            console.log(`Task ${taskNumber}: Transcribe URL:`, transcribeUrl);

            if (!transcribeUrl) {
                console.error(`Task ${taskNumber}: Transcribe URL is undefined`);
                alert('Error: Transcription service URL is not configured. Please refresh the page or contact support.');
                return;
            }

            console.log(`Task ${taskNumber}: Starting recording, transcribe URL: ${transcribeUrl}`);

            try {
                if (!navigator.mediaDevices || !MediaRecorder) {
                    throw new Error('MediaRecorder is not supported in this browser.');
                }

                console.log(`Task ${taskNumber}: Requesting microphone access`);
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                console.log(`Task ${taskNumber}: Microphone access granted`);

                mediaRecorder = new MediaRecorder(stream);
                const chunks = [];
                isRecording = true;

                playbackElement.classList.add('d-none');
                audioElement.src = '';
                transcriptionInput.value = '';
                transcriptionElement.textContent = '';
                transcriptionElement.classList.add('d-none');
                soundwaveElement.classList.add('d-none');
                stopButton.classList.add('d-none');

                this.disabled = true;
                this.textContent = 'Preparing...';
                startTimer(taskNumber, preparationTime / 1000, 'preparing', async () => {
                    this.textContent = 'Recording...';
                    stopButton.classList.remove('d-none');
                    soundwaveElement.classList.remove('d-none');
                    timerElement.classList.remove('timer-preparing');

                    mediaRecorder.start();
                    console.log(`Task ${taskNumber}: Recording started`);
                    mediaRecorder.ondataavailable = e => chunks.push(e.data);
                    mediaRecorder.onstop = async () => {
                        isRecording = false;
                        audioBlobs[taskNumber] = new Blob(chunks, { type: 'audio/webm' });
                        audioElement.src = URL.createObjectURL(audioBlobs[taskNumber]);
                        playbackElement.classList.remove('d-none');
                        soundwaveElement.classList.add('d-none');
                        stopButton.classList.add('d-none');
                        this.textContent = 'Start Recording';
                        this.disabled = false;
                        stopTimer(taskNumber);
                        stream.getTracks().forEach(track => track.stop());
                        console.log(`Task ${taskNumber}: Recording stopped, audio ready`);

                        try {
                            const formData = new FormData();
                            formData.append('audio', audioBlobs[taskNumber], `task_${taskNumber}.webm`);
                            formData.append('csrf_token', form.querySelector('input[name="csrf_token"]').value);
                            console.log(`Task ${taskNumber}: Sending audio to ${transcribeUrl}`);
                            const response = await fetch(transcribeUrl, {
                                method: 'POST',
                                body: formData
                            });
                            if (!response.ok) {
                                const errorText = await response.text();
                                console.error(`Task ${taskNumber}: Transcription failed with status ${response.status}: ${errorText}`);
                                throw new Error(`HTTP ${response.status}: ${errorText}`);
                            }
                            const data = await response.json();
                            if (data.error) {
                                throw new Error(data.error);
                            }
                            transcriptions[taskNumber] = data.transcription;
                            transcriptionElement.textContent = data.transcription;
                            transcriptionElement.classList.remove('d-none');
                            transcriptionInput.value = data.transcription;
                            console.log(`Task ${taskNumber}: Transcription received: ${data.transcription.substring(0, 50)}...`);
                            checkAllTasksCompleted();
                        } catch (error) {
                            console.error(`Task ${taskNumber} transcription error:`, error);
                            alert('Error transcribing audio: ' + error.message);
                        }
                    };

                    startTimer(taskNumber, responseTime / 1000, 'recording', () => {
                        if (mediaRecorder.state === 'recording') {
                            mediaRecorder.stop();
                        }
                    });
                });

                stopButton.addEventListener('click', () => {
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        stopTimer(taskNumber);
                        console.log(`Task ${taskNumber}: Recording manually stopped`);
                    }
                }, { once: true });

            } catch (error) {
                isRecording = false;
                console.error(`Task ${taskNumber} recording error:`, error);
                alert('Error starting recording: ' + error.message);
                this.textContent = 'Start Recording';
                this.disabled = false;
                stopTimer(taskNumber);
                soundwaveElement.classList.add('d-none');
                stopButton.classList.add('d-none');
            }
        });
    });

    document.getElementById('submit-all-tasks').addEventListener('click', async () => {
        const submitButton = document.getElementById('submit-all-tasks');
        const submitUrl = container.dataset.submitUrl;
        const resultsUrl = container.dataset.resultsUrl;

        console.log(`Submit URL: ${submitUrl}, Results URL: ${resultsUrl}`);

        if (!submitUrl) {
            console.error('Submit URL is undefined');
            alert('Error: Submission service is not configured. Please contact support.');
            return;
        }

        console.log(`Submitting all tasks to ${submitUrl}`);

        submitButton.disabled = true;
        submitButton.textContent = 'Submitting...';

        try {
            const formData = new FormData();
            const setName = document.querySelector('input[name="set_name"]').value;
            formData.append('set_name', setName);
            formData.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);
            Object.keys(transcriptions).forEach(taskNumber => {
                formData.append(`transcription_${taskNumber}`, transcriptions[taskNumber]);
                formData.append(`task_number_${taskNumber}`, taskNumber);
            });

            const response = await fetch(submitUrl, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Submission failed with status ${response.status}: ${errorText}`);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            let alertMessage = `Your Speaking Test Results for Set ${setName}:\n\n`;
            data.scores.forEach((score, index) => {
                alertMessage += `Task ${index + 1}:\n`;
                alertMessage += `  • Fluency: ${score.fluency}/9\n`;
                alertMessage += `  • Coherence: ${score.coherence}/9\n`;
                alertMessage += `  • Vocabulary: ${score.vocabulary}/9\n`;
                alertMessage += `  • Pronunciation: ${score.pronunciation}/9\n`;
                alertMessage += `  • Task Score: ${score.overall.toFixed(1)}/9\n\n`;
            });
            alertMessage += `Overall Test Score: ${data.overall_score.toFixed(2)}/9`;
            alert(alertMessage);
            window.location.href = resultsUrl;
        } catch (error) {
            console.error('Submission error:', error);
            alert('Error submitting speaking test: ' + error.message);
            submitButton.disabled = false;
            submitButton.textContent = 'Submit All Tasks';
        }
    });
});