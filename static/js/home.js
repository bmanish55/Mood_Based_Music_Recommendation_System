document.addEventListener('DOMContentLoaded', function() {
    // ======================
    // 1. INITIALIZATION
    // ======================
    const moodModal = new bootstrap.Modal(document.getElementById('moodModal'));
    const youtubeModal = new bootstrap.Modal(document.getElementById('youtubeModal'));
    const moodModalTitle = document.getElementById('moodModalTitle');
    const moodDetectionMessage = document.getElementById('moodDetectionMessage');
    const playlistResults = document.getElementById('playlistResults');
    const playlistItems = document.querySelector('.playlist-items');
    const savePlaylistBtn = document.getElementById('savePlaylistBtn');
    const loadingSpinner = document.querySelector('#moodDetectionContent .spinner-border');
    const youtubePlayer = document.getElementById('youtubePlayer');
    const youtubeModalTitle = document.getElementById('youtubeModalTitle');
    const faceDetectionBtn = document.getElementById('faceDetectionBtn');
    const imageUploadBtn = document.querySelector('.image-upload-btn');
    const imageUploadInput = document.getElementById('imageUploadInput');
    const typeMoodBtn = document.querySelector('.type-mood-btn');
    const ctaBtn = document.getElementById('ctaBtn');
    const cameraSection = document.getElementById('cameraSection');
    const cameraPreview = document.getElementById('cameraPreview');
    const captureButton = document.getElementById('captureButton');
    const retryButton = document.getElementById('retryButton');
    const statusMessage = document.getElementById('statusMessage');

    let stream = null;
    let currentMood = null;
    let currentTrack = null; // To store current track for favorite functionality

    // Profile dropdown functionality
    const userProfile = document.getElementById('userProfile');
    const profileDropdown = document.getElementById('profileDropdown');
    if (userProfile) {
        userProfile.addEventListener('click', function(e) {
            e.stopPropagation();
            profileDropdown.classList.toggle('show');
        });
        document.addEventListener('click', function() {
            profileDropdown.classList.remove('show');
        });
        profileDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    // ======================
    // 2. CORE FUNCTIONS
    // ======================
    function showMoodModal(title, message, showCamera = false) {
        moodModalTitle.textContent = title;
        moodDetectionMessage.textContent = message;
        playlistResults.classList.add('d-none');
        playlistItems.innerHTML = '';
        loadingSpinner.classList.remove('d-none');
        cameraSection.classList.toggle('d-none', !showCamera);
        moodDetectionContent.classList.toggle('d-none', showCamera);
        moodModal.show();
    }

    function stopCameraStream() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
            cameraPreview.srcObject = null;
        }
    }

    function showStatus(message, type = 'info') {
        statusMessage.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    }

    function handleCameraError(error) {
        console.error('Camera error:', error);
        stopCameraStream();
        let errorMessage = 'Could not access camera.';
        if (error.name === 'NotAllowedError') {
            errorMessage = 'Camera access was denied. Please allow camera permissions.';
        } else if (error.name === 'NotFoundError') {
            errorMessage = 'No camera device found.';
        } else if (error.name === 'NotReadableError') {
            errorMessage = 'Camera is already in use by another application.';
        }
        showStatus(errorMessage, 'danger');
        retryButton.classList.remove('d-none');
    }

    // ======================
    // 3. FACE DETECTION
    // ======================
    async function startFaceDetection() {
        showMoodModal('Face Emotion Detection', 'Preparing camera...', true);
        retryButton.classList.add('d-none');
        statusMessage.innerHTML = '';
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false
            });
            cameraPreview.srcObject = stream;
            captureButton.disabled = false;
        } catch (error) {
            handleCameraError(error);
        }
    }

    async function captureFaceImage() {
        if (!stream) return;
        try {
            captureButton.disabled = true;
            const canvas = document.createElement('canvas');
            canvas.width = cameraPreview.videoWidth;
            canvas.height = cameraPreview.videoHeight;
            canvas.getContext('2d').drawImage(cameraPreview, 0, 0, canvas.width, canvas.height);
            stopCameraStream();
            showMoodModal('Face Emotion Detection', 'Analyzing your expression...');
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('image', blob, 'face-capture.jpg');
                try {
                    const response = await fetch('/detect/face', {
                        method: 'POST',
                        body: formData,
                        credentials: 'same-origin'
                    });
                    const data = await response.json();
                    if (response.ok && data.status === 'success') {
                        displayPlaylist(data.emotion, data.tracks);
                    } else {
                        showStatus(data.message || 'Error detecting emotion', 'danger');
                        retryButton.classList.remove('d-none');
                    }
                } catch (error) {
                    console.error('Detection error:', error);
                    showStatus('Error analyzing expression. Please try again.', 'danger');
                    retryButton.classList.remove('d-none');
                }
            }, 'image/jpeg', 0.9);
        } catch (error) {
            console.error('Capture error:', error);
            showStatus('Error capturing image. Please try again.', 'danger');
            retryButton.classList.remove('d-none');
        }
    }

    // ======================
    // 4. YOUTUBE PLAYER
    // ======================
    function getYouTubeId(url) {
        const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
        const match = url.match(regExp);
        return (match && match[2].length === 11) ? match[2] : null;
    }

    function playYouTubeVideo(url, title, artist) {
        const videoId = getYouTubeId(url);
        if (!videoId) {
            showStatus('Invalid YouTube URL', 'danger');
            return;
        }
        youtubePlayer.src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
        youtubeModalTitle.textContent = title || 'Now Playing';
        currentTrack = { url, title, artist };
        youtubeModal.show();
        if (currentMood) {
            recordSongPlayed(currentMood, title, artist || 'Unknown Artist', url);
        }
    }

    function recordSongPlayed(mood, songTitle, artist, url) {
        fetch('/record-played-song', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mood, song_title: songTitle, artist, url }),
            credentials: 'same-origin'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Song play recorded in history');
                } else {
                    console.error('Failed to record song play:', data.error);
                }
            })
            .catch(error => console.error('Error recording song play:', error));
    }

    // ======================
    // 5. PLAYLIST DISPLAY
    // ======================
    function displayPlaylist(emotion, tracks) {
        loadingSpinner.classList.add('d-none');
        playlistItems.innerHTML = '';
        if (!Array.isArray(tracks) || tracks.length === 0) {
            playlistItems.innerHTML = `<div class="alert alert-warning">No valid tracks found. Please try another detection method.</div>`;
            return;
        }
        const validTracks = tracks.filter(track => track?.name && track?.url);
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
        document.querySelectorAll('.play-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const url = this.getAttribute('data-url');
                const title = this.getAttribute('data-title');
                const artist = this.getAttribute('data-artist');
                playYouTubeVideo(url, title, artist);
            });
        });
        moodDetectionMessage.textContent = `We detected you're feeling ${emotion}. Here are some recommendations:`;
        playlistResults.classList.remove('d-none');
        savePlaylistBtn.classList.remove('d-none');
        currentMood = emotion.toLowerCase();
    }

    // ======================
    // 6. IMAGE UPLOAD
    // ======================
    if (imageUploadBtn && imageUploadInput) {
        imageUploadBtn.addEventListener('click', () => imageUploadInput.click());
        imageUploadInput.addEventListener('change', async function(e) {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                const previewContainer = document.getElementById('imagePreviewContainer');
                const previewImage = document.getElementById('uploadedImagePreview');
                if (previewContainer && previewImage) {
                    const reader = new FileReader();
                    reader.onload = e => {
                        previewImage.src = e.target.result;
                        previewContainer.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
                showMoodModal('Image Analysis', 'Analyzing your uploaded image...');
                const formData = new FormData();
                formData.append('image', file);
                try {
                    const response = await fetch('/detect/image', {
                        method: 'POST',
                        body: formData,
                        credentials: 'same-origin'
                    });
                    const data = await response.json();
                    if (response.ok && data.status === 'success') {
                        displayPlaylist(data.emotion, data.tracks);
                    } else {
                        moodDetectionMessage.textContent = data.message || 'Error analyzing image. Please try another image.';
                        retryButton.classList.remove('d-none');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    moodDetectionMessage.textContent = 'Error connecting to server. Please try again.';
                    retryButton.classList.remove('d-none');
                }
            }
        });
    }

    // ======================
    // 7. TEXT MOOD INPUT
    // ======================
    if (typeMoodBtn) {
        typeMoodBtn.addEventListener('click', async () => {
            const userMood = prompt("How are you feeling today? (e.g., happy, sad, excited, relaxed)");
            if (userMood && userMood.length >= 3) {
                showMoodModal('Mood Analysis', 'Analyzing your mood...');
                try {
                    const response = await fetch('/detect/text', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `text=${encodeURIComponent(userMood)}`,
                        credentials: 'same-origin'
                    });
                    const data = await response.json();
                    if (response.ok && data.status === 'success') {
                        displayPlaylist(data.emotion, data.tracks);
                    } else {
                        moodDetectionMessage.textContent = data.message || 'Error analyzing your mood. Please try again.';
                        retryButton.classList.remove('d-none');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    moodDetectionMessage.textContent = 'Error connecting to server. Please try again.';
                    retryButton.classList.remove('d-none');
                }
            } else {
                alert('Please enter at least 3 characters to describe your mood.');
            }
        });
    }

    // ======================
    // 8. ADD TO FAVORITES
    // ======================
    document.querySelectorAll('.add-to-favorites-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!currentTrack) {
                alert('No track selected.');
                return;
            }
            try {
                const response = await fetch('/add_to_favorites', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: currentTrack.title,
                        artist: currentTrack.artist,
                        url: currentTrack.url
                    }),
                    credentials: 'same-origin'
                });
                const data = await response.json();
                alert(data.message || (data.success ? 'Song added to favorites!' : 'Failed to add song to favorites.'));
            } catch (error) {
                console.error('Error adding to favorites:', error);
                alert('Error connecting to server. Please try again.');
            }
        });
    });

    // ======================
    // 9. EVENT LISTENERS
    // ======================
    if (ctaBtn) ctaBtn.addEventListener('click', startFaceDetection);
    if (faceDetectionBtn) faceDetectionBtn.addEventListener('click', startFaceDetection);
    if (captureButton) captureButton.addEventListener('click', captureFaceImage);
    if (retryButton) {
        retryButton.addEventListener('click', () => {
            retryButton.classList.add('d-none');
            statusMessage.innerHTML = '';
            startFaceDetection();
        });
    }
    if (moodModal) {
        moodModal._element.addEventListener('hidden.bs.modal', () => {
            stopCameraStream();
            statusMessage.innerHTML = '';
            retryButton.classList.add('d-none');
            currentMood = null;
            currentTrack = null;
        });
    }
    if (youtubeModal) {
        youtubeModal._element.addEventListener('hidden.bs.modal', () => {
            youtubePlayer.src = '';
            currentTrack = null;
        });
    }
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && stream) {
            stopCameraStream();
        }
    });

    // Smooth Scrolling for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});