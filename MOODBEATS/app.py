from flask import Flask, render_template, request, jsonify,flash, url_for, send_from_directory,redirect,session
from werkzeug.utils import secure_filename
from textblob import TextBlob
import fer
import os
import time
import requests
from dotenv import load_dotenv
import cv2
import numpy as np
import base64
import json
from flask_cors import CORS
from functools import wraps  # Add this import
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'vishal',
    'database': 'moodbeats'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # If user is already logged in, redirect to dashboard
        if 'user_id' in session:
            return redirect(url_for('loginhome'))
        return render_template('login.html')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'message': 'Invalid username or password'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
    
    return redirect(url_for('login_page'))

@app.route('/register', methods=['POST'])
def register():
    if 'user_id' in session:
            return redirect(url_for('dashboard'))
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Insert new user
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/dashboard')
@login_required
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/loginhome')  # This defines the URL path as /loginhome
@login_required
def loginhome():  # This is the function name that url_for() should reference
    return render_template('loginhome.html',
                         username=session['username'],
                         user_image=url_for('static', filename='img/user.png'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#API Connetion
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# YouTube Music API credentials
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Mood to YouTube Music search queries mapping
MOOD_QUERIES = {
    'happy': 'happy music playlist',
    'sad': 'sad songs playlist', 
    'angry': 'angry rock music playlist',
    'relaxed': 'chill music playlist',
    'neutral': 'popular music playlist',
    'surprise': 'upbeat music playlist',
    'fear': 'calming music playlist',
    'disgust': 'hard rock music playlist'
}

# Initialize FER detector
emotion_detector = fer.FER()

class YouTubeMusicAPI:
    def __init__(self):
        self.api_key = YOUTUBE_API_KEY
    
    def search_videos(self, query, max_results=5):
        """Search YouTube for music videos"""
        if not self.api_key:
            print("YouTube API key not configured")
            return []
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'videoCategoryId': '10',  # Music category
            'maxResults': max_results,
            'key': self.api_key
        }
        
        try:
            print(f"Searching YouTube for: {query}")
            response = requests.get(url, params=params)
            print(f"YouTube API Response: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return []
                
            data = response.json()
            
            # Debugging output
            print(f"Raw API response: {json.dumps(data, indent=2)}")
            
            videos = []
            for item in data.get('items', []):
                if not item.get('id', {}).get('videoId'):
                    continue
                    
                thumbnails = item.get('snippet', {}).get('thumbnails', {})
                thumbnail = thumbnails.get('default', {}).get('url') if thumbnails else None
                
                videos.append({
                    'name': item.get('snippet', {}).get('title', 'Unknown Track'),
                    'artist': item.get('snippet', {}).get('channelTitle', 'Unknown Artist'),
                    'url': f"https://music.youtube.com/watch?v={item['id']['videoId']}",
                    'image': thumbnail or 'https://via.placeholder.com/40'
                })
            
            print(f"Successfully processed {len(videos)} videos")
            return videos[:max_results]
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching YouTube: {e}")
            return []
        except (KeyError, TypeError) as e:
            print(f"Error processing YouTube data: {e}")
            return []

# Initialize YouTube Music API helper
youtube_music = YouTubeMusicAPI()

def detect_emotion_from_image(image_path):
    """Detect emotion from an image using FER with better error handling"""
    try:
        print(f"Processing image at: {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not read image at {image_path}")
            return 'neutral'
            
        print(f"Image dimensions: {image.shape}")
        # Convert to RGB (FER expects RGB)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect emotions
        results = emotion_detector.detect_emotions(image_rgb)
        if not results:
            print("No emotions detected in image")
            return 'neutral'
        
        # Get dominant emotion
        emotions = results[0]['emotions']
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
        print(f"Detected emotion: {dominant_emotion}")
        return dominant_emotion
        
    except Exception as e:
        print(f"Error detecting emotion: {e}")
        return 'neutral'

def detect_emotion_from_text(text):
    #convert capital to lower find mood keyword
    lower_text = text.lower()
    
    # Mood keywords
    mood_keywords = ['happy', 'relaxed', 'neutral', 'sad', 'angry']

    # Check if any mood word is in the text
    for mood in mood_keywords:
        if mood in lower_text:
            return mood
    try:
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        
        if polarity > 0.5:
            return 'happy'
        elif 0.2 < polarity <= 0.5:
            return 'relaxed'
        elif -0.2 <= polarity <= 0.2:
            return 'neutral'
        elif -0.5 < polarity < -0.2:
            return 'sad'
        else:  # polarity <= -0.5
            return 'angry'
    except Exception as e:
        print(f"Error analyzing text: {e}")
        return 'neutral'

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('loginhome'))
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/detect/face', methods=['POST'])
def detect_face_emotion():
    """Detect emotion from webcam capture with improved error handling"""
    if 'image' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No image provided',
            'error_code': 400
        }), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No selected file',
            'error_code': 400
        }), 400
    
    try:
        # Save the file temporarily3
        filename = secure_filename(f"face_{int(time.time())}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Detect emotion
        emotion = detect_emotion_from_image(filepath)
        print(f"Detected emotion from face: {emotion}")
        
        # Get YouTube Music videos
        query = MOOD_QUERIES.get(emotion, MOOD_QUERIES['neutral'])
        videos = youtube_music.search_videos(query)
        print(f"Found {len(videos)} videos for query {query}")
        
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return jsonify({
            'status': 'success',
            'emotion': emotion,
            'tracks': videos,
            'query': query,
            'count': len(videos)
        })
        
    except Exception as e:
        print(f"Error in face detection: {str(e)}")
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            'status': 'error',
            'message': 'Failed to process face detection',
            'error': str(e),
            'error_code': 500
        }), 500

@app.route('/detect/text', methods=['POST'])
def detect_text_emotion():
    """Detect emotion from text input with improved validation"""
    text = request.form.get('text', '').strip()
    if not text or len(text) < 3:
        return jsonify({
            'status': 'error',
            'message': 'Please enter at least 3 characters',
            'error_code': 400
        }), 400
    
    try:
        emotion = detect_emotion_from_text(text)
        print(f"Detected emotion from text: {emotion}")
        
        query = MOOD_QUERIES.get(emotion, MOOD_QUERIES['neutral'])
        videos = youtube_music.search_videos(query)
        print(f"Found {len(videos)} videos for query {query}")
        
        return jsonify({
            'status': 'success',
            'emotion': emotion,
            'tracks': videos,
            'query': query,
            'count': len(videos)
        })
        
    except Exception as e:
        print(f"Error in text detection: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to analyze text',
            'error': str(e),
            'error_code': 500
        }), 500

@app.route('/detect/image', methods=['POST'])
def detect_image_emotion():
    """Detect emotion from uploaded image with improved file handling"""
    if 'image' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No image provided',
            'error_code': 400
        }), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No selected file',
            'error_code': 400
        }), 400
    
    try:
        # Save the uploaded file
        filename = secure_filename(f"img_{int(time.time())}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Detect emotion
        emotion = detect_emotion_from_image(filepath)
        print(f"Detected emotion from image: {emotion}")
        
        # Get YouTube Music videos
        query = MOOD_QUERIES.get(emotion, MOOD_QUERIES['neutral'])
        videos = youtube_music.search_videos(query)
        print(f"Found {len(videos)} videos for query {query}")
        
        return jsonify({
            'status': 'success',
            'emotion': emotion,
            'tracks': videos,
            'image_url': url_for('static', filename=f'uploads/{filename}'),
            'query': query,
            'count': len(videos)
        })
        
    except Exception as e:
        print(f"Error in image detection: {str(e)}")
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            'status': 'error',
            'message': 'Failed to process image',
            'error': str(e),
            'error_code': 500
        }), 500

@app.route('/history-data')
def history_data():
    """Endpoint to fetch user's mood history data in JSON format"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get user_id from session if available, otherwise query it
        user_id = session.get('user_id')
        if not user_id:
            cursor.execute("SELECT id FROM users WHERE username = %s", (session['username'],))
            user = cursor.fetchone()
            user_id = user['id'] if user else None
        
        if user_id:
            query = """
                SELECT 
                    h.id, 
                    h.mood, 
                    h.playedsong, 
                    h.song_artist,
                    h.song_url,
                    h.day_date 
                FROM history h
                WHERE h.user_id = %s 
                ORDER BY h.day_date DESC
                LIMIT 50
            """
            cursor.execute(query, (user_id,))
            history_data = cursor.fetchall()
            
            # Convert datetime to ISO format string for JSON serialization
            for entry in history_data:
                entry['day_date'] = entry['day_date'].isoformat() if entry['day_date'] else None
                # Ensure all fields have values
                entry['song_artist'] = entry.get('song_artist', 'Unknown Artist')
                entry['song_url'] = entry.get('song_url', '')
        else:
            history_data = []
        
        cursor.close()
        connection.close()
        
        return jsonify(history_data)
    
    except Exception as e:
        print(f"Error fetching history data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/record-played-song', methods=['POST'])
def record_played_song():
    """Endpoint to record a played song with mood in history"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        mood = data.get('mood')
        song_title = data.get('song_title')
        artist = data.get('artist', 'Unknown Artist')
        url = data.get('url', '')
        
        # Validate required fields
        if not mood or not song_title:
            return jsonify({'success': False, 'error': 'Mood and song title are required'}), 400
        
        # Get user_id from session
        user_id = session.get('user_id')
        if not user_id:
            # Fallback to query user_id if not in session
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE username = %s", (session['username'],))
            user = cursor.fetchone()
            user_id = user['id'] if user else None
            cursor.close()
            connection.close()
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User not found'}), 404
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            # Insert into history table with all available data
            query = """
                INSERT INTO history 
                    (user_id, mood, playedsong, song_artist, song_url, day_date)
                VALUES 
                    (%s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(query, (
                user_id, 
                mood, 
                song_title, 
                artist, 
                url
            ))
            connection.commit()
            
            # Get the inserted record ID
            history_id = cursor.lastrowid
            
            return jsonify({
                'success': True,
                'history_id': history_id
            })
            
        except Exception as e:
            connection.rollback()
            raise e
            
        finally:
            cursor.close()
            connection.close()
            
    except Exception as e:
        print(f"Error recording played song: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'message': 'Failed to record song in history'
        }), 500
    
@app.route('/get_playlist_songs/<int:playlist_id>')
def get_playlist_songs(playlist_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify playlist belongs to user
        cursor.execute("SELECT user_id FROM playlists WHERE id = %s", (playlist_id,))
        playlist = cursor.fetchone()
        
        if not playlist or playlist['user_id'] != session['user_id']:
            return jsonify({'error': 'Playlist not found'}), 404
        
        # Get songs in playlist with their order
        cursor.execute("""
            SELECT s.* 
            FROM songs s
            JOIN playlist_songs ps ON s.id = ps.song_id
            WHERE ps.playlist_id = %s
            ORDER BY ps.position ASC
        """, (playlist_id,))
        
        songs = cursor.fetchall()
        return jsonify(songs)
        
    except Exception as e:
        print("Error fetching playlist songs:", e)
        return jsonify({'error': 'Failed to load playlist songs'}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@app.route('/playlists')
def playlists():
    if 'user_id' not in session:
        return redirect('/login')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user's playlists with song count
        cursor.execute("""
            SELECT p.*, COUNT(ps.song_id) as song_count 
            FROM playlists p
            LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id
            WHERE p.user_id = %s
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """, (session['user_id'],))
        
        playlists = cursor.fetchall()
        
        # Get default cover if none exists
        for playlist in playlists:
            if not playlist['cover_image']:
                playlist['cover_image'] = 'default_playlist.jpg'
        
        return render_template('dashboard.html',
                            playlists=playlists,
                            active_page='playlists')
        
    except Exception as e:
        print("Error fetching playlists:", e)
        flash('Error loading playlists', 'error')
        return render_template('dashboard.html',
                            playlists=[],
                            active_page='playlists')
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    if 'user_id' not in session:
        return redirect('/login')
    
    playlist_name = request.form.get('playlist_name')
    if not playlist_name:
        flash('Playlist name is required', 'error')
        return redirect('/playlists')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO playlists (user_id, name, cover_image)
            VALUES (%s, %s, %s)
        """, (session['user_id'], playlist_name, 'default_playlist.jpg'))
        
        conn.commit()
        flash('Playlist created successfully!', 'success')
        return redirect('/playlists')
        
    except Exception as e:
        print("Error creating playlist:", e)
        flash('Error creating playlist', 'error')
        return redirect('/playlists')
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@app.template_filter('time_ago')
def time_ago_filter(dt):
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days // 365} years ago"
    if diff.days > 30:
        return f"{diff.days // 30} months ago"
    if diff.days > 0:
        return f"{diff.days} days ago"
    if diff.seconds > 3600:
        return f"{diff.seconds // 3600} hours ago"
    if diff.seconds > 60:
        return f"{diff.seconds // 60} minutes ago"
    return "just now"

@app.route('/settings')
def settings():
    if 'username' not in session:
        return redirect('/login')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT username, email FROM users WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_data:
            flash('User not found', 'error')
            return redirect('/')
            
        return render_template('dashboard.html', user_data=user_data, active_page='settings')
    
    except Exception as e:
        print("Error fetching user settings:", e)
        flash('Error loading settings', 'error')
        return redirect('/')

@app.route('/update_account', methods=['POST'])
def update_account():
    if 'username' not in session:
        return redirect('/login')
    
    new_username = request.form.get('username')
    new_email = request.form.get('email')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username or email already exists
        cursor.execute("SELECT id FROM users WHERE (username = %s OR email = %s) AND id != %s", 
                      (new_username, new_email, session['user_id']))
        if cursor.fetchone():
            flash('Username or email already exists', 'error')
            return redirect('/settings')
        
        # Update account info
        cursor.execute("UPDATE users SET username = %s, email = %s WHERE id = %s", 
                      (new_username, new_email, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update session username if changed
        if new_username != session['username']:
            session['username'] = new_username
        
        flash('Account information updated successfully', 'success')
        return redirect('/settings')
    
    except Exception as e:
        print("Error updating account:", e)
        flash('Error updating account information', 'error')
        return redirect('/settings')

@app.route('/update_password', methods=['POST'])
def update_password():
    if 'username' not in session:
        return redirect('/login')
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect('/settings')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify current password
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password_hash'], current_password):
            flash('Current password is incorrect', 'error')
            return redirect('/settings')
        
        # Update password
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", 
                      (generate_password_hash(new_password), session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Password updated successfully', 'success')
        return redirect('/settings')
    
    except Exception as e:
        print("Error updating password:", e)
        flash('Error updating password', 'error')
        return redirect('/settings')
              
if __name__ == '__main__':
    # Ensure all required directories exist
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/img', exist_ok=True)
    app.run(debug=True)