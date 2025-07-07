// AI Assistant Frontend JavaScript

// DOM Elements
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const emotionText = document.getElementById('emotion-text');
const emotionEmoji = document.getElementById('emotion-emoji');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const conversation = document.getElementById('conversation');
const voiceText = document.getElementById('voice-text');
const aiResponse = document.getElementById('ai-response');
const imageGallery = document.getElementById('image-gallery');
const audioPlayer = document.getElementById('audio-player');
const playBtn = document.getElementById('play-btn');
const pauseBtn = document.getElementById('pause-btn');
const audioProgress = document.getElementById('audio-progress');
const audioProgressBar = document.getElementById('audio-progress-bar');
const audioCurrentTime = document.getElementById('audio-current-time');
const audioDuration = document.getElementById('audio-duration');

// Global variables
let stream = null;
let websocket = null;
let isRunning = false;
let captureInterval = null;
let recognitionActive = false;
let clientId = generateClientId();
let currentEmotion = 'neutral';

// Speech recognition
let recognition = null;
let recognitionTimeout = null;

// Initialize speech recognition
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
    } else if ('SpeechRecognition' in window) {
        recognition = new SpeechRecognition();
    } else {
        console.warn('Speech recognition not supported');
        return false;
    }
    
    // Configure recognition
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    // Set up event handlers
    recognition.onresult = handleSpeechResult;
    
    recognition.onend = () => {
        if (recognitionActive) {
            // Restart recognition after a short delay
            recognitionTimeout = setTimeout(() => {
                try {
                    recognition.start();
                    console.log('Speech recognition restarted');
                } catch (error) {
                    console.error('Error restarting speech recognition:', error);
                }
            }, 500);
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        updateStatus('error', `Speech error: ${event.error}`);
        
        // Restart on error after a delay
        if (recognitionActive && event.error !== 'aborted' && event.error !== 'no-speech') {
            clearTimeout(recognitionTimeout);
            recognitionTimeout = setTimeout(() => {
                try {
                    recognition.start();
                    console.log('Speech recognition restarted after error');
                } catch (error) {
                    console.error('Error restarting speech recognition:', error);
                }
            }, 2000);
        }
    };
    
    return true;
}

// Emotion to emoji mapping
const emotionEmojis = {
    'angry': '😠',
    'disgust': '🤢',
    'fear': '😨',
    'happy': '😊',
    'sad': '😢',
    'surprise': '😲',
    'neutral': '😐'
};

// Initialize the application
function init() {
    // Event listeners
    startBtn.addEventListener('click', startAssistant);
    stopBtn.addEventListener('click', stopAssistant);
    
    // Initialize speech recognition
    initSpeechRecognition();
    
    // Set up audio player events
    audioPlayer.addEventListener('play', () => {
        updateStatus('speaking', 'Speaking...');
        playBtn.classList.add('hidden');
        pauseBtn.classList.remove('hidden');
    });
    
    audioPlayer.addEventListener('pause', () => {
        playBtn.classList.remove('hidden');
        pauseBtn.classList.add('hidden');
    });
    
    audioPlayer.addEventListener('ended', () => {
        updateStatus('active', 'Connected');
        playBtn.classList.remove('hidden');
        pauseBtn.classList.add('hidden');
        audioProgressBar.style.width = '0%';
        audioCurrentTime.textContent = '0:00';
    });
    
    audioPlayer.addEventListener('timeupdate', updateAudioProgress);
    
    audioPlayer.addEventListener('loadedmetadata', () => {
        audioDuration.textContent = formatTime(audioPlayer.duration);
    });
    
    // Audio control buttons
    playBtn.addEventListener('click', () => {
        audioPlayer.play();
    });
    
    pauseBtn.addEventListener('click', () => {
        audioPlayer.pause();
    });
    
    // Audio progress bar click event
    audioProgress.addEventListener('click', (e) => {
        const rect = audioProgress.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        audioPlayer.currentTime = pos * audioPlayer.duration;
    });
    
    // Check if camera is available
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            // Release the stream immediately, we just wanted to check access
            stream.getTracks().forEach(track => track.stop());
            updateStatus('ready', 'Ready');
        })
        .catch(error => {
            console.error('Camera access error:', error);
            updateStatus('error', 'Camera access denied');
        });
}

// Generate a unique client ID
function generateClientId() {
    return 'client_' + Math.random().toString(36).substring(2, 15);
}

// Start the assistant
async function startAssistant() {
    try {
        // Update UI first to show we're starting
        updateStatus('starting', 'Starting assistant...');
        
        // Reset any previous state
        isRunning = true;
        
        // Clear previous elements
        voiceText.textContent = '';
        aiResponse.textContent = '';
        imageGallery.innerHTML = '';
        audioPlayer.src = '';
        
        // Start camera
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
        } catch (cameraError) {
            console.error('Camera error:', cameraError);
            updateStatus('error', `Camera error: ${cameraError.message}`);
            // Continue without camera if needed
        }
        
        // Connect WebSocket
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            // Close existing connection first
            try {
                websocket.close();
            } catch (e) {
                console.error('Error closing existing WebSocket:', e);
            }
        }
        connectWebSocket();
        
        // Start speech recognition
        if (recognition) {
            try {
                recognitionActive = true;
                recognition.start();
                console.log('Speech recognition started');
            } catch (speechError) {
                console.error('Speech recognition error:', speechError);
                // Try to reinitialize speech recognition
                if (initSpeechRecognition()) {
                    try {
                        recognition.start();
                    } catch (e) {
                        console.error('Failed to restart speech recognition:', e);
                    }
                }
            }
        }
        
        // Start capturing frames if camera is available
        if (stream) {
            startCapturing();
        }
        
        // Update UI
        startBtn.classList.add('hidden');
        stopBtn.classList.remove('hidden');
        updateStatus('active', 'Assistant active');
        
        // Add system message to conversation
        addMessage('system', 'Assistant is now active. Please speak clearly.');
        
    } catch (error) {
        console.error('Error starting assistant:', error);
        updateStatus('error', `Error: ${error.message}`);
        isRunning = false;
    }
}

// Stop the assistant
function stopAssistant() {
    // Update UI first
    updateStatus('stopping', 'Stopping assistant...');
    
    // Stop camera
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }
    
    // Stop capturing frames
    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
    
    // Stop speech recognition
    if (recognition) {
        try {
            recognitionActive = false;
            recognition.stop();
            
            // Clear any pending recognition timeouts
            if (recognitionTimeout) {
                clearTimeout(recognitionTimeout);
                recognitionTimeout = null;
            }
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
        }
    }
    
    // Close WebSocket if it's open
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        try {
            // Simply close the WebSocket without sending a stop message
            websocket.close();
            console.log('WebSocket connection closed');
        } catch (error) {
            console.error('Error closing WebSocket:', error);
        }
    }
    
    // Update UI
    startBtn.classList.remove('hidden');
    stopBtn.classList.add('hidden');
    isRunning = false;
    
    // Add system message to conversation
    addMessage('system', 'Assistant stopped.');
    
    // Change status to ready
    updateStatus('ready', 'Ready');
}

// This function has been removed as part of disabling the final response functionality
// Keeping this comment as a placeholder in case the functionality needs to be restored later

// Then move all these functions outside and at the same level as startAssistant and stopAssistant
// Connect to WebSocket
function connectWebSocket() {
    // Get the current host
    const host = window.location.host;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    // Create WebSocket connection
    websocket = new WebSocket(`${protocol}//${host}/ws/emotion/${clientId}`);

    // WebSocket event handlers
    websocket.onopen = () => {
        console.log('WebSocket connected');
        updateStatus('active', 'Connected');
    };

    websocket.onclose = (event) => {
        console.log('WebSocket disconnected with code:', event.code);
        
        // If the connection is lost during an active session, attempt to reconnect
        if (isRunning) {
            updateStatus('error', 'Connection lost');
            // Try to reconnect after a delay
            setTimeout(connectWebSocket, 3000);
        }
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('error', 'Connection error');
    };

    websocket.onmessage = (event) => {
        handleWebSocketMessage(event);
    };
}

// Start capturing frames
function startCapturing() {
    captureInterval = setInterval(() => {
        if (isRunning && video.readyState === 4) {
            captureFrame();
        }
    }, 1000); // Capture every second
}

// Capture a frame from the video
function captureFrame() {
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to base64 image
    const imageData = canvas.toDataURL('image/jpeg', 0.7);

    // Send image to server via WebSocket
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ image: imageData }));
    }
}

// Handle speech recognition results
function handleSpeechResult(event) {
    const results = event.results;
    let finalTranscript = '';
    let interimTranscript = '';

    for (let i = event.resultIndex; i < results.length; i++) {
        const transcript = results[i][0].transcript;
    
        if (results[i].isFinal) {
            finalTranscript += transcript;
        } else {
            interimTranscript += transcript;
        }
    }

    // Update voice text display
    if (interimTranscript) {
        voiceText.innerHTML = `<em>${interimTranscript}</em>`;
    }

    // Process final transcript
    if (finalTranscript) {
        voiceText.textContent = finalTranscript;
    
        // Send text to server via WebSocket
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({ text: finalTranscript }));
            updateStatus('processing', 'Processing...');
        
            // Add user message to conversation
            addMessage('user', finalTranscript);
        }
    }
}

// Handle WebSocket messages
function handleWebSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);
        console.log('Received message:', data);
    
        switch (data.type) {
            case 'emotion':
                updateEmotion(data.emotion);
                break;
            
            case 'ai_response':
                handleAIResponse(data.response);
                updateStatus('active', 'Connected');
                break;
            
            case 'audio':
                playAudio(data.url);
                break;
                
            case 'final_response':
                // Ignore final responses as we've disabled this feature
                console.log('Received final_response but ignoring as per updated functionality');
                updateStatus('ready', 'Ready');
                break;
                
            case 'stop_acknowledged':
                // Server acknowledged stop request
                console.log('Server acknowledged stop request');
                updateStatus('ready', 'Ready');
                break;
            
            case 'error':
                console.error('Server error:', data.message);
                updateStatus('error', `Error: ${data.message}`);
                break;
            
            default:
                console.log('Unknown message type:', data.type);
        }
    } catch (error) {
        console.error('Error parsing WebSocket message:', error);
    }
}

// Update emotion display
function updateEmotion(emotion) {
    currentEmotion = emotion;
    emotionText.textContent = emotion.charAt(0).toUpperCase() + emotion.slice(1);
    emotionEmoji.textContent = emotionEmojis[emotion] || '😐';

    // Update emotion classes
    Object.keys(emotionEmojis).forEach(e => {
        emotionText.classList.remove(`emotion-${e}`);
    });
    emotionText.classList.add(`emotion-${emotion}`);
}

// Handle AI response
function handleAIResponse(response) {
    // Display AI response text
    aiResponse.textContent = response.result || 'No response';

    // Add AI message to conversation
    addMessage('ai', response.result);

    // Display images
    displayImages(response.images || []);
}

// Display images in the gallery
function displayImages(images) {
    // Clear existing images
    imageGallery.innerHTML = '';

    // Add new images
    images.forEach(image => {
        const container = document.createElement('div');
        container.className = 'image-container cursor-pointer';
    
        const img = document.createElement('img');
        img.src = image.image_url;
        img.alt = 'AI generated image';
        img.loading = 'lazy';
    
        // Make image clickable to show popup
        container.addEventListener('click', () => {
            showImagePopup(image.image_url, image.source_url);
        });
    
        container.appendChild(img);
        imageGallery.appendChild(container);
    });

    // If no images, show a message
    if (images.length === 0) {
        imageGallery.innerHTML = '<p class="text-gray-500 text-center p-4">No images available</p>';
    }
}

// Play audio from URL
function playAudio(url) {
    audioPlayer.src = url;
    audioPlayer.play().catch(error => {
        console.error('Error playing audio:', error);
    });
}

// Add a message to the conversation
function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'user' ? 'user-message self-end' :
        type === 'ai' ? 'ai-message self-start' :
            'bg-gray-200 p-3 rounded-lg text-center';

    // Add timestamp
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Format message based on type
    if (type === 'user') {
        messageDiv.innerHTML = `
        <div class="flex justify-between items-center mb-1">
            <span class="font-medium text-blue-600">You</span>
            <span class="text-xs text-gray-500">${timestamp}</span>
        </div>
        <p>${text}</p>
    `;
    } else if (type === 'ai') {
        messageDiv.innerHTML = `
        <div class="flex justify-between items-center mb-1">
            <span class="font-medium text-green-600">AI Assistant</span>
            <span class="text-xs text-gray-500">${timestamp}</span>
        </div>
        <p>${text}</p>
    `;
    } else {
        // System message
        messageDiv.innerHTML = `
        <p>${text}</p>
        <span class="text-xs text-gray-500">${timestamp}</span>
    `;
    }

    conversation.appendChild(messageDiv);

    // Scroll to bottom
    conversation.scrollTop = conversation.scrollHeight;
}

// Update status indicator
function updateStatus(status, message) {
    // Remove all status classes
    statusIndicator.classList.remove('status-active', 'status-listening', 'status-processing', 'status-error', 'status-ready', 'status-starting', 'status-stopping', 'status-speaking');

    // Add appropriate class
    statusIndicator.classList.add(`status-${status}`);

    // Update status text
    statusText.textContent = message;
}

// Update audio progress bar
function updateAudioProgress() {
    if (audioPlayer.duration) {
        const percentage = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        audioProgressBar.style.width = `${percentage}%`;
        audioCurrentTime.textContent = formatTime(audioPlayer.currentTime);
    }
}

// Format time in MM:SS format
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
}

// Show image popup
function showImagePopup(imageUrl, sourceUrl) {
    // Create popup overlay
    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-4';
    overlay.id = 'image-popup-overlay';
    
    // Create popup content container
    const popupContent = document.createElement('div');
    popupContent.className = 'relative max-w-4xl w-full bg-white rounded-lg shadow-lg p-2';
    
    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'absolute top-2 right-2 bg-red-600 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-red-700';
    closeBtn.innerHTML = '<i class="fas fa-times"></i>';
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        document.body.removeChild(overlay);
    });
    
    // Create image element
    const img = document.createElement('img');
    img.src = imageUrl;
    img.className = 'max-h-[80vh] max-w-full mx-auto rounded-lg';
    img.alt = 'Enlarged image';
    
    // Create footer with source link
    const footer = document.createElement('div');
    footer.className = 'mt-2 text-center';
    
    if (sourceUrl) {
        const sourceLink = document.createElement('a');
        sourceLink.href = sourceUrl;
        sourceLink.target = '_blank';
        sourceLink.className = 'text-blue-600 hover:underline';
        sourceLink.textContent = 'Open original source';
        sourceLink.addEventListener('click', (e) => {
            e.stopPropagation(); // Don't close the popup when clicking the link
        });
        footer.appendChild(sourceLink);
    }
    
    // Assemble popup
    popupContent.appendChild(closeBtn);
    popupContent.appendChild(img);
    popupContent.appendChild(footer);
    overlay.appendChild(popupContent);
    
    // Close popup when clicking outside the image
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            document.body.removeChild(overlay);
        }
    });
    
    // Add to document
    document.body.appendChild(overlay);
    
    // Handle escape key to close popup
    const handleEscKey = (e) => {
        if (e.key === 'Escape') {
            if (document.body.contains(overlay)) {
                document.body.removeChild(overlay);
            }
            document.removeEventListener('keydown', handleEscKey);
        }
    };
    
    document.addEventListener('keydown', handleEscKey);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);

// Handle page unload
window.addEventListener('beforeunload', () => {
    // Clean up resources
    stopAssistant();
});