// Wait for the DOM to be fully loaded before executing JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    // ======================
    // 1. INITIALIZATION
    // ======================
    
    // Initialize Bootstrap tooltips for all elements with data-bs-toggle="tooltip"
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // ======================
    // 2. ELEMENT SELECTORS
    // ======================
    
    // Mood Detection Modal Elements
    const moodModal = new bootstrap.Modal(document.getElementById('moodModal'));
    const youtubeModal = new bootstrap.Modal(document.getElementById('youtubeModal'));
    const moodModalTitle = document.getElementById('moodModalTitle');
    const moodDetectionMessage = document.getElementById('moodDetectionMessage');
    const playlistResults = document.getElementById('playlistResults');
    const playlistItems = document.querySelector('.playlist-items');
    const loadingSpinner = document.querySelector('#moodDetectionContent .spinner-border');
    const youtubePlayer = document.getElementById('youtubePlayer');
    const youtubeModalTitle = document.getElementById('youtubeModalTitle');

    // Feature Buttons
    const faceDetectionBtn = document.getElementById('faceDetectionBtn');
    const imageUploadBtn = document.querySelector('.image-upload-btn');
    const imageUploadInput = document.getElementById('imageUploadInput');
    const typeMoodBtn = document.querySelector('.type-mood-btn');
    const ctaBtn = document.getElementById('ctaBtn');

    // Face Detection Elements
    const cameraSection = document.getElementById('cameraSection');
    const cameraPreview = document.getElementById('cameraPreview');
    const captureButton = document.getElementById('captureButton');
    const retryButton = document.getElementById('retryButton');
    const statusMessage = document.getElementById('statusMessage');
    
    // State Variables
    let stream = null; // To store the camera stream
    let currentMood = null; // To track the current mood selection

    // ======================
    // 3. CORE FUNCTIONS
    // ======================
    
    /**
     * Shows the mood modal with specific content
     * @param {string} title - Modal title
     * @param {string} message - Message to display
     * @param {boolean} showCamera - Whether to show camera section
     */
    function showMoodModal(title, message, showCamera = false) {
        // Set modal title and message
        moodModalTitle.textContent = title;
        moodDetectionMessage.textContent = message;
        
        // Reset modal state
        playlistResults.classList.add('d-none');
        playlistItems.innerHTML = '';
        loadingSpinner.classList.remove('d-none');
        
        // Handle camera section visibility
        if (showCamera) {
            cameraSection.classList.remove('d-none');
            moodDetectionContent.classList.add('d-none');
        } else {
            cameraSection.classList.add('d-none');
            moodDetectionContent.classList.remove('d-none');
        }
        
        // Show the modal
        moodModal.show();
    }

    /**
     * Stops the camera stream if active
     */
    function stopCameraStream() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
    }

    /**
     * Displays status messages in the UI
     * @param {string} message - Message to display
     * @param {string} type - Alert type (info, success, danger, etc.)
     */
    function showStatus(message, type = 'info') {
        statusMessage.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    }

    /**
     * Handles camera errors with appropriate messages
     * @param {Error} error - The error object
     */
    function handleCameraError(error) {
        console.error('Camera error:', error);
        stopCameraStream();
        
        // Determine appropriate error message
        let errorMessage = 'Could not access camera.';
        if (error.name === 'NotAllowedError') {
            errorMessage = 'Camera access was denied. Please allow camera permissions.';
        } else if (error.name === 'NotFoundError') {
            errorMessage = 'No camera device found.';
        } else if (error.name === 'NotReadableError') {
            errorMessage = 'Camera is already in use by another application.';
        }
        
        // Show error and enable retry button
        showStatus(errorMessage, 'danger');
        retryButton.classList.remove('d-none');
    }

    // ======================
    // 4. FACE DETECTION
    // ======================
    
    /**
     * Starts the face detection process by accessing the camera
     */
    async function startFaceDetection() {
        // Prepare UI for camera access
        showMoodModal('Face Emotion Detection', 'Preparing camera...', true);
        retryButton.classList.add('d-none');
        statusMessage.innerHTML = '';
        
        try {
            // Request camera access with preferred settings
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'user', // Use front camera
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                },
                audio: false
            });
            
            // Display camera feed
            cameraPreview.srcObject = stream;
            captureButton.disabled = false;
            
        } catch (error) {
            handleCameraError(error);
        }
    }

    /**
     * Captures the current frame and sends it to the server for analysis
     */
    async function captureFaceImage() {
        if (!stream) return;
        
        try {
            // Disable capture button during processing
            captureButton.disabled = true;
            
            // Create canvas to capture the current frame
            const canvas = document.createElement('canvas');
            canvas.width = cameraPreview.videoWidth;
            canvas.height = cameraPreview.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(cameraPreview, 0, 0, canvas.width, canvas.height);
            
            // Stop the camera stream
            stopCameraStream();
            
            // Show analyzing message
            showMoodModal('Face Emotion Detection', 'Analyzing your expression...');
            
            // Convert canvas to JPEG blob
            canvas.toBlob(async (blob) => {
                // Prepare form data for server request
                const formData = new FormData();
                formData.append('image', blob, 'face-capture.jpg');
                
                try {
                    // Send image to server for analysis
                    const response = await fetch('/detect/face', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok && data.status === 'success') {
                        // Display results if successful
                        displayPlaylist(data.emotion, data.tracks);
                    } else {
                        throw new Error(data.message || 'Error detecting emotion');
                    }
                } catch (error) {
                    console.error('Detection error:', error);
                    showStatus(error.message || 'Error analyzing expression. Please try again.', 'danger');
                    retryButton.classList.remove('d-none');
                }
            }, 'image/jpeg', 0.9); // 0.9 quality
            
        } catch (error) {
            console.error('Capture error:', error);
            showStatus('Error capturing image. Please try again.', 'danger');
            retryButton.classList.remove('d-none');
        }
    }

    // ======================
    // 5. YOUTUBE PLAYER
    // ======================
    
    /**
     * Extracts YouTube video ID from URL
     * @param {string} url - YouTube URL
     * @returns {string|null} Video ID or null if invalid
     */
    function getYouTubeId(url) {
        const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
        const match = url.match(regExp);
        return (match && match[2].length === 11) ? match[2] : null;
    }

    /**
     * Plays YouTube video in modal
     * @param {string} url - YouTube URL
     * @param {string} title - Video title
     * @param {string} artist - Artist name
     */
    function playYouTubeVideo(url, title, artist) {
        const videoId = getYouTubeId(url);
        if (!videoId) {
            alert('Invalid YouTube URL');
            return;
        }
        
        // Set up YouTube player
        youtubePlayer.src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
        youtubeModalTitle.textContent = title || 'Now Playing';
        youtubeModal.show();
    }

    // ======================
    // 6. PLAYLIST DISPLAY
    // ======================
    
    /**
     * Displays recommended playlist in the modal
     * @param {string} emotion - Detected emotion
     * @param {Array} tracks - Array of track objects
     */
    function displayPlaylist(emotion, tracks) {
        // Hide loading spinner
        loadingSpinner.classList.add('d-none');
        playlistItems.innerHTML = '';
        
        // Validate tracks data
        if (!Array.isArray(tracks)) {
            playlistItems.innerHTML = `
                <div class="alert alert-danger">
                    Invalid track data received. Please try again.
                </div>
            `;
            return;
        }
        
        // Filter valid tracks
        const validTracks = tracks.filter(track => track?.name && track?.url);
        
        if (validTracks.length === 0) {
            playlistItems.innerHTML = `
                <div class="alert alert-warning">
                    No valid tracks found. Please try another detection method.
                </div>
            `;
            return;
        }
        
        // Display each track
        validTracks.forEach(track => {
            const item = document.createElement('div');
            item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div class="d-flex align-items-center">
                    <img src="${track.image || 'https://via.placeholder.com/40'}" 
                         class="rounded me-3" 
                         width="40" 
                         height="40"
                         onerror="this.src='https://via.placeholder.com/40'">
                    <div>
                        <h6 class="mb-1">${track.name || 'Unknown Track'}</h6>
                        <small class="text-muted">${track.artist || 'Unknown Artist'}</small>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-danger play-btn" 
                        data-url="${track.url}" 
                        data-title="${track.name}"
                        data-artist="${track.artist || 'Unknown Artist'}">
                    <i class="fas fa-play"></i> Play
                </button>
            `;
            playlistItems.appendChild(item);
        });
        
        // Add click handlers to play buttons
        document.querySelectorAll('.play-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const url = this.getAttribute('data-url');
                const title = this.getAttribute('data-title');
                const artist = this.getAttribute('data-artist');
                playYouTubeVideo(url, title, artist);
            });
        });
        
        // Update UI with results
        moodDetectionMessage.textContent = `We detected you're feeling ${emotion}. Here are some recommendations:`;
        playlistResults.classList.remove('d-none');
        currentMood = emotion.toLowerCase();
    }

    // ======================
    // 7. IMAGE UPLOAD
    // ======================
    
    if (imageUploadBtn && imageUploadInput) {
        imageUploadBtn.addEventListener('click', function() {
            imageUploadInput.click();
        });
        
        imageUploadInput.addEventListener('change', async function(e) {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                
                // Show image preview if elements exist
                const previewContainer = document.getElementById('imagePreviewContainer');
                const previewImage = document.getElementById('uploadedImagePreview');
                
                if (previewContainer && previewImage) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        previewImage.src = e.target.result;
                        previewContainer.style.display = 'block';
                    }
                    reader.readAsDataURL(file);
                }
                
                // Show analyzing message
                showMoodModal('Image Analysis', `Analyzing your uploaded image...`);
                
                // Prepare and send image to server
                const formData = new FormData();
                formData.append('image', file);
                
                try {
                    const response = await fetch('/detect/image', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    console.log("Image detection response:", data);
                    
                    if (response.ok && data.status === 'success') {
                        displayPlaylist(data.emotion, data.tracks);
                    } else {
                        moodDetectionMessage.textContent = data.message || 'Error analyzing image. Please try another image.';
                    }
                } catch (error) {
                    console.error('Error:', error);
                    moodDetectionMessage.textContent = 'Error connecting to server. Please try again.';
                }
            }
        });
    }

    // ======================
    // 8. TEXT MOOD INPUT
    // ======================
    
    if (typeMoodBtn) {
        typeMoodBtn.addEventListener('click', async function() {
            const userMood = prompt("How are you feeling today? (e.g., happy, sad, excited, relaxed)");
            if (userMood) {
                showMoodModal('Mood Analysis', `Analyzing your mood...`);
                
                try {
                    const response = await fetch('/detect/text', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `text=${encodeURIComponent(userMood)}`
                    });
                    
                    const data = await response.json();
                    console.log("Text detection response:", data);
                    
                    if (response.ok && data.status === 'success') {
                        displayPlaylist(data.emotion, data.tracks);
                    } else {
                        moodDetectionMessage.textContent = data.message || 'Error analyzing your mood. Please try again.';
                    }
                } catch (error) {
                    console.error('Error:', error);
                    moodDetectionMessage.textContent = 'Error connecting to server. Please try again.';
                }
            }
        });
    }

    // ======================
    // 9. EVENT LISTENERS
    // ======================
    
    // CTA Button
    if (ctaBtn) {
        ctaBtn.addEventListener('click', startFaceDetection);
    }

    // Face Detection Buttons
    if (faceDetectionBtn) {
        faceDetectionBtn.addEventListener('click', startFaceDetection);
    }
    if (captureButton) {
        captureButton.addEventListener('click', captureFaceImage);
    }
    if (retryButton) {
        retryButton.addEventListener('click', () => {
            retryButton.classList.add('d-none');
            statusMessage.innerHTML = '';
            startFaceDetection();
        });
    }

    // Modal Cleanup
    const moodModalElement = document.getElementById('moodModal');
    if (moodModalElement) {
        moodModalElement.addEventListener('hidden.bs.modal', () => {
            stopCameraStream();
            statusMessage.innerHTML = '';
            retryButton.classList.add('d-none');
        });
    }

    // YouTube Modal Cleanup
    if (youtubeModal) {
        youtubeModal._element.addEventListener('hidden.bs.modal', function() {
            if (youtubePlayer) youtubePlayer.src = '';
        });
    }

    // Page Visibility Changes
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && stream) {
            stopCameraStream();
        }
    });

    // ======================
    // 10. FORM HANDLING
    // ======================
    
    // Newsletter Form
    const newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const emailInput = this.querySelector('input[type="email"]');
            if (emailInput) {
                const email = emailInput.value;
                console.log('Subscribed email:', email);
                alert('Thank you for subscribing to our newsletter!');
                this.reset();
            }
        });
    }

    // ======================
    // 11. UTILITY FUNCTIONS
    // ======================
    
    // Smooth Scrolling for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});