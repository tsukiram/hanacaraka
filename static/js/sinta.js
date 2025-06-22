// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\sinta.js
document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const newChatForm = document.getElementById('newChatForm');
    const chatForm = document.getElementById('chatForm');
    const chatContainer = document.getElementById('chat-container');
    const chatTitle = document.getElementById('chat-title');
    const recordBtn = document.getElementById('recordBtn');
    const audioInput = document.getElementById('audio');
    const messageInput = document.getElementById('message');
    const sendBtn = document.getElementById('sendBtn');
    const recordingIndicator = document.getElementById('recordingIndicator');
    const transcriptionPreview = document.getElementById('transcriptionPreview');
    const transcriptionText = document.getElementById('transcriptionText');
    const copyTranscriptionBtn = document.getElementById('copyTranscriptionBtn');
    const chatHistory = document.getElementById('chatHistory');
    const correctionModal = new bootstrap.Modal(document.getElementById('correctionModal'));
    const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    // State variables
    let currentSessionId = null;
    let mediaRecorder = null;
    let audioChunks = [];
    let sessionToDelete = null;

    // Initialize event listeners
    initEventListeners();

    function initEventListeners() {
        // New chat form submission
        newChatForm.addEventListener('submit', handleNewChatSubmit);

        // Load existing chat session
        chatHistory.addEventListener('click', (e) => {
            const loadLink = e.target.closest('.load-session');
            if (loadLink) {
                e.preventDefault();
                loadSession(loadLink.dataset.sessionId);
            }
        });

        // Delete chat session
        chatHistory.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('.delete-session');
            if (deleteBtn) {
                e.preventDefault();
                sessionToDelete = deleteBtn.dataset.sessionId;
                deleteConfirmModal.show();
            }
        });

        // Confirm delete
        confirmDeleteBtn.addEventListener('click', handleDeleteSession);

        // Chat form submission
        chatForm.addEventListener('submit', handleChatSubmit);

        // Audio recording
        recordBtn.addEventListener('click', handleRecordClick);

        // Copy transcription to input
        copyTranscriptionBtn.addEventListener('click', () => {
            messageInput.value = transcriptionText.textContent;
            messageInput.focus();
            sendBtn.disabled = false;
        });

        // Enable send button when input is not empty
        messageInput.addEventListener('input', () => {
            sendBtn.disabled = !messageInput.value.trim();
        });
    }

    async function handleNewChatSubmit(e) {
        e.preventDefault();
        const topic = document.getElementById('topic').value;
        const csrfToken = newChatForm.querySelector('input[name="csrf_token"]').value;
        try {
            const response = await fetch('/sinta/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({ topic })
            });
            const data = await response.json();
            if (response.ok) {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.dataset.sessionId = data.session_id;
                li.innerHTML = `
                    <div>
                        <a href="#" class="load-session" data-session-id="${data.session_id}">${data.title}</a>
                        <small class="text-muted d-block">${new Date().toLocaleString()}</small>
                    </div>
                    <button type="button" class="btn btn-outline-danger btn-sm delete-session" data-session-id="${data.session_id}" aria-label="Delete chat">
                        <i class="bi bi-trash"></i>
                    </button>`;
                chatHistory.prepend(li);
                loadSession(data.session_id, data.initial_message);
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error('Error creating new chat:', error);
            alert('Failed to create new chat');
        }
    }

    async function handleDeleteSession() {
        if (!sessionToDelete) return;
        const csrfToken = chatForm.querySelector('input[name="csrf_token"]').value;
        try {
            const response = await fetch(`/sinta/delete/${sessionToDelete}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRF-Token': csrfToken
                }
            });
            const data = await response.json();
            if (response.ok) {
                const sessionItem = chatHistory.querySelector(`li[data-session-id="${sessionToDelete}"]`);
                if (sessionItem) sessionItem.remove();
                if (currentSessionId === sessionToDelete) {
                    currentSessionId = null;
                    chatTitle.textContent = 'Select or start a chat';
                    chatContainer.innerHTML = '<div class="recording-indicator" id="recordingIndicator" style="display: none;"><span class="wave"></span><span class="wave"></span><span class="wave"></span>Recording...</div>';
                }
                deleteConfirmModal.hide();
                sessionToDelete = null;
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error('Error deleting session:', error);
            alert('Failed to delete session');
        }
    }

    async function loadSession(sessionId, initialMessage = null) {
        currentSessionId = sessionId;
        try {
            const response = await fetch(`/sinta/chat/${sessionId}`);
            const data = await response.json();
            if (response.ok) {
                chatTitle.textContent = data.session.title;
                chatContainer.innerHTML = '<div class="recording-indicator" id="recordingIndicator" style="display: none;"><span class="wave"></span><span class="wave"></span><span class="wave"></span>Recording...</div>';
                if (initialMessage) {
                    appendMessage(initialMessage);
                    data.messages.forEach(msg => {
                        if (!(msg.role === 'assistant' && msg.content === initialMessage.content && !msg.input_raw)) {
                            appendMessage(msg);
                        }
                    });
                } else {
                    data.messages.forEach(msg => {
                        appendMessage(msg);
                    });
                }
                chatContainer.scrollTop = chatContainer.scrollHeight;
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error('Error loading session:', error);
            alert('Failed to load session');
        }
    }

    function appendMessage(msg) {
        const div = document.createElement('div');
        div.className = `message-${msg.role}`;
        let html = `<strong>${msg.role === 'user' ? 'You' : 'Sinta'}:</strong> ${msg.content}<br>
                    <small class="text-muted">${new Date(msg.timestamp).toLocaleString()}</small>`;
        if (msg.role === 'user' && msg.input_raw && (msg.error_tags || msg.correction_tags || msg.variants)) {
            html += `<br><span class="correction-btn" data-input-raw="${msg.input_raw}" 
                        data-error-tags="${msg.error_tags || ''}" 
                        data-correction-tags="${msg.correction_tags || ''}" 
                        data-casual-variant="${msg.variants ? msg.variants.casual : ''}" 
                        data-formal-variant="${msg.variants ? msg.variants.formal : ''}">Show Corrections</span>`;
        }
        div.innerHTML = html;
        chatContainer.appendChild(div);

        const correctionBtn = div.querySelector('.correction-btn');
        if (correctionBtn) {
            correctionBtn.addEventListener('click', () => {
                document.getElementById('modal-input-raw').textContent = correctionBtn.dataset.inputRaw;
                const errorText = correctionBtn.dataset.errorTags.replace(/\[rr\[(.*?)\]rr\]/g, '<span class="error-text">$1</span>');
                const correctionText = correctionBtn.dataset.correctionTags.replace(/\[gg\[(.*?)\]gg\]/g, '<span class="corrected-text">$1</span>');
                document.getElementById('modal-error-tags').innerHTML = errorText;
                document.getElementById('modal-correction-tags').innerHTML = correctionText;
                document.getElementById('modal-casual-variant').textContent = correctionBtn.dataset.casualVariant;
                document.getElementById('modal-formal-variant').textContent = correctionBtn.dataset.formalVariant;
                correctionModal.show();
            });
        }
    }

    async function handleChatSubmit(e) {
        e.preventDefault();
        if (!currentSessionId) {
            alert('Please select or create a chat session');
            return;
        }
        const formData = new FormData(chatForm);
        const csrfToken = chatForm.querySelector('input[name="csrf_token"]').value;
        try {
            sendBtn.disabled = true;
            const response = await fetch(`/sinta/chat/${currentSessionId}`, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrfToken
                },
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                appendMessage({ 
                    role: 'user', 
                    content: formData.get('message') || data.input_raw, 
                    input_raw: data.input_raw, 
                    error_tags: data.error_tags, 
                    correction_tags: data.correction_tags, 
                    variants: data.variants, 
                    timestamp: new Date().toISOString() 
                });
                appendMessage({
                    role: 'assistant',
                    content: data.output,
                    timestamp: new Date().toISOString()
                });
                chatContainer.scrollTop = chatContainer.scrollHeight;
                chatForm.reset();
                resetTranscriptionPreview();
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message');
        } finally {
            sendBtn.disabled = !messageInput.value.trim();
        }
    }

    async function handleRecordClick() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            recordBtn.classList.remove('recording');
            recordBtn.textContent = '🎙️ Record';
            recordBtn.setAttribute('aria-label', 'Record audio');
            recordingIndicator.style.display = 'none';
            transcriptionPreview.style.display = 'block';
            transcriptionText.textContent = 'Processing audio...';
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
                    await transcribeAudio(audioFile);
                };
                mediaRecorder.start();
                recordBtn.classList.add('recording');
                recordBtn.textContent = '⏹️ Stop';
                recordBtn.setAttribute('aria-label', 'Stop recording');
                recordingIndicator.style.display = 'block';
                sendBtn.disabled = true;
                resetTranscriptionPreview();
            } catch (error) {
                console.error('Error accessing microphone:', error);
                alert('Failed to access microphone');
                sendBtn.disabled = !messageInput.value.trim();
            }
        }
    }

    async function transcribeAudio(audioFile) {
        const formData = new FormData();
        formData.append('audio', audioFile);
        const csrfToken = chatForm.querySelector('input[name="csrf_token"]').value;
        try {
            const response = await fetch(`/sinta/transcribe`, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrfToken
                },
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                transcriptionText.textContent = data.transcription || 'No transcription available';
                transcriptionPreview.style.display = 'block';
                sendBtn.disabled = !messageInput.value.trim();
            } else {
                transcriptionText.textContent = 'Error transcribing audio';
                alert(data.error);
                sendBtn.disabled = !messageInput.value.trim();
            }
        } catch (error) {
            console.error('Error transcribing audio:', error);
            transcriptionText.textContent = 'Error transcribing audio';
            alert('Failed to transcribe audio');
            sendBtn.disabled = !messageInput.value.trim();
        }
    }

    function resetTranscriptionPreview() {
        transcriptionPreview.style.display = 'none';
        transcriptionText.textContent = '';
    }
});