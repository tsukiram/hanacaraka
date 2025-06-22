// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\sinta.js
document.addEventListener('DOMContentLoaded', () => {
    const newChatForm = document.getElementById('newChatForm');
    const chatForm = document.getElementById('chatForm');
    const chatContainer = document.getElementById('chat-container');
    const chatTitle = document.getElementById('chat-title');
    const recordBtn = document.getElementById('recordBtn');
    const audioInput = document.getElementById('audio');
    const correctionModal = new bootstrap.Modal(document.getElementById('correctionModal'));
    let currentSessionId = null;
    let mediaRecorder = null;
    let audioChunks = [];

    // Create new chat session
    newChatForm.addEventListener('submit', async (e) => {
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
                li.className = 'list-group-item';
                li.innerHTML = `<a href="#" class="load-session" data-session-id="${data.session_id}">${data.title}</a>
                                <small class="text-muted">${new Date().toLocaleString()}</small>`;
                document.querySelector('.list-group').prepend(li);
                loadSession(data.session_id, data.initial_message);
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error('Error creating new chat:', error);
            alert('Failed to create new chat');
        }
    });

    // Load existing chat session
    document.querySelectorAll('.load-session').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            loadSession(link.dataset.sessionId);
        });
    });

    async function loadSession(sessionId, initialMessage = null) {
        currentSessionId = sessionId;
        try {
            const response = await fetch(`/sinta/chat/${sessionId}`);
            const data = await response.json();
            if (response.ok) {
                chatTitle.textContent = data.session.title;
                chatContainer.innerHTML = '';
                if (initialMessage) {
                    appendMessage(initialMessage);
                    // Skip the first assistant message from data.messages if it matches initialMessage
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

        // Add event listener for correction button
        const correctionBtn = div.querySelector('.correction-btn');
        if (correctionBtn) {
            correctionBtn.addEventListener('click', () => {
                document.getElementById('modal-input-raw').textContent = correctionBtn.dataset.inputRaw;
                // Replace [rr[]rr] and [gg[]gg] with colored spans, keep other text normal
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

    // Handle chat form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!currentSessionId) {
            alert('Please select or create a chat session');
            return;
        }
        const formData = new FormData(chatForm);
        const csrfToken = chatForm.querySelector('input[name="csrf_token"]').value;
        try {
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
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message');
        }
    });

    // Handle audio recording
    recordBtn.addEventListener('click', async () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            recordBtn.textContent = '🎙️ Record';
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
                    audioInput.files = new DataTransfer().files;
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(audioFile);
                    audioInput.files = dataTransfer.files;
                    recordBtn.textContent = '🎙️ Record';
                };
                mediaRecorder.start();
                recordBtn.textContent = '⏹️ Stop';
            } catch (error) {
                console.error('Error accessing microphone:', error);
                alert('Failed to access microphone');
            }
        }
    });
});