from flask import Flask, render_template, request, jsonify, flash, url_for, send_from_directory, redirect, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from textblob import TextBlob
import fer
import os
import time
import requests
from dotenv import load_dotenv
import cv2
import mysql.connector
from functools import wraps
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
CORS(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'vishal',
    'database': 'moodbeats'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# YouTube Music API credentials
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Mood to YouTube Music search queries mapping with colors
MOOD_QUERIES = {
    'happy': {'query': 'happy music playlist', 'color': '#ffd700'},
    'sad': {'query': 'sad songs playlist', 'color': '#4682b4'},
    'angry': {'query': 'angry rock music playlist', 'color': '#dc3545'},
    'relaxed': {'query': 'chill music playlist', 'color': '#32cd32'},
    'neutral': {'query': 'popular music playlist', 'color': '#6c757d'},
    'surprise': {'query': 'upbeat music playlist', 'color': '#ff69b4'},
    'fear': {'query': 'calming music playlist', 'color': '#4b0082'},
    'disgust': {'query': 'hard rock music playlist', 'color': '#8b4513'}
}

# Initialize FER detector
emotion_detector = fer.FER()

# YouTube Music API class
class YouTubeMusicAPI:
    def __init__(self):
        self.api_key = YOUTUBE_API_KEY
    
    def search_videos(self, query, max_results=10):
        if not self.api_key:
            print("YouTube API key not configured")
            return []
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'videoCategoryId': '10',
            'maxResults': max_results,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return []
                
            data = response.json()
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
            return videos[:max_results]
        except (requests.exceptions.RequestException, KeyError, TypeError) as e:
            print(f"Error processing YouTube data: {e}")
            return []

youtube_music = YouTubeMusicAPI()

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login to access the admin panel', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('loginhome'))
        return render_template('login.html')
    
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
        return jsonify({'success': False, 'message': 'Invalid username or password'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/register', methods=['POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('loginhome'))
    
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Username already exists'})
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email already registered'})
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
        cursor.close()
        conn.close()

@app.route('/loginhome')
@login_required
def loginhome():
    return render_template('loginhome.html', username=session['username'])

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT COUNT(*) as count FROM favorites WHERE user_id = %s', (session['user_id'],))
    total_favorites = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM playlists WHERE user_id = %s', (session['user_id'],))
    total_playlists = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM songs')
    total_songs = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    # Fetch songs for each mood
    mood_songs = {}
    for mood, data in MOOD_QUERIES.items():
        mood_songs[mood] = youtube_music.search_videos(data['query'], max_results=10)
    
    return render_template('dashboard.html',
                         username=session['username'],
                         user_image=url_for('static', filename='img/user.png'),
                         total_favorites=total_favorites,
                         total_playlists=total_playlists,
                         total_songs=total_songs,
                         mood_songs=mood_songs,
                         mood_queries=MOOD_QUERIES,
                         active_page='dashboard')

@app.route('/favorites')
@login_required
def favorites():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT f.id, s.title, s.artist, s.url 
        FROM favorites f 
        JOIN songs s ON f.song_id = s.id 
        WHERE f.user_id = %s
    ''', (session['user_id'],))
    favorites = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('favorites.html', username=session['username'], favorites=favorites, active_page='favorites')

@app.route('/add_to_favorites', methods=['POST'])
@login_required
def add_to_favorites():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        title = data.get('title')
        artist = data.get('artist', 'Unknown Artist')
        url = data.get('url')
        
        if not title or not url:
            return jsonify({'success': False, 'error': 'Title and URL are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if song exists
        cursor.execute('SELECT id FROM songs WHERE url = %s', (url,))
        song = cursor.fetchone()
        
        if not song:
            # Insert new song
            cursor.execute(
                'INSERT INTO songs (title, artist, url) VALUES (%s, %s, %s)',
                (title, artist, url)
            )
            song_id = cursor.lastrowid
        else:
            song_id = song[0]
        
        # Check if already in favorites
        cursor.execute(
            'SELECT id FROM favorites WHERE user_id = %s AND song_id = %s',
            (session['user_id'], song_id)
        )
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Song already in favorites'}), 400
        
        # Add to favorites
        cursor.execute(
            'INSERT INTO favorites (user_id, song_id) VALUES (%s, %s)',
            (session['user_id'], song_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Song added to favorites'})
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to add song to favorites'
        }), 500

@app.route('/delete_favorite/<int:favorite_id>', methods=['POST'])
@login_required
def delete_favorite(favorite_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM favorites WHERE id = %s AND user_id = %s', (favorite_id, session['user_id']))
        conn.commit()
        flash('Song removed from favorites', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error removing favorite: {str(err)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('favorites'))

@app.route('/playlists', methods=['GET', 'POST'])
@login_required
def playlists():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        playlist_name = request.form.get('playlist_name')
        if playlist_name:
            try:
                cursor.execute(
                    'INSERT INTO playlists (user_id, name, song_count) VALUES (%s, %s, %s)',
                    (session['user_id'], playlist_name, 0)
                )
                conn.commit()
                flash('Playlist created successfully', 'success')
            except mysql.connector.Error as err:
                conn.rollback()
                flash(f'Error creating playlist: {str(err)}', 'danger')
    
    cursor.execute('SELECT id, name, song_count, created_at FROM playlists WHERE user_id = %s', (session['user_id'],))
    playlists = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('playlists.html', username=session.get('username', 'User'), playlists=playlists, active_page='playlists')

@app.route('/add_songs_to_playlist/<int:playlist_id>', methods=['GET', 'POST'])
@login_required
def add_songs_to_playlist(playlist_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify playlist exists and belongs to the user
    cursor.execute('SELECT id, name FROM playlists WHERE id = %s AND user_id = %s', (playlist_id, session['user_id']))
    playlist = cursor.fetchone()
    if not playlist:
        flash('Playlist not found or unauthorized', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('playlists'))
    
    if request.method == 'POST':
        selected_song_ids = request.form.getlist('song_ids')
        print(f"Selected song IDs: {selected_song_ids}")  # Debugging
        if not selected_song_ids:
            flash('No songs selected', 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('add_songs_to_playlist', playlist_id=playlist_id))
        
        try:
            # Get existing songs in the playlist
            cursor.execute('SELECT song_id FROM playlist_songs WHERE playlist_id = %s', (playlist_id,))
            existing_song_ids = {row['song_id'] for row in cursor.fetchall()}
            
            # Validate selected song IDs
            placeholders = ','.join(['%s'] * len(selected_song_ids))
            cursor.execute(f'SELECT id FROM songs WHERE id IN ({placeholders})', tuple(int(id) for id in selected_song_ids))
            valid_song_ids = {row['id'] for row in cursor.fetchall()}
            print(f"Valid song IDs: {valid_song_ids}")  # Debugging
            
            new_songs = 0
            for song_id in selected_song_ids:
                song_id = int(song_id)
                if song_id not in valid_song_ids:
                    flash(f'Song ID {song_id} is invalid', 'danger')
                    continue
                if song_id not in existing_song_ids:
                    cursor.execute(
                        'INSERT INTO playlist_songs (playlist_id, song_id) VALUES (%s, %s)',
                        (playlist_id, song_id)
                    )
                    new_songs += 1
            
            if new_songs > 0:
                cursor.execute(
                    'UPDATE playlists SET song_count = song_count + %s WHERE id = %s',
                    (new_songs, playlist_id)
                )
                conn.commit()
                flash(f'{new_songs} song(s) added to playlist', 'success')
            else:
                flash('No new songs added (all selected songs already in playlist or invalid)', 'info')
            print(f"New songs added: {new_songs}")  # Debugging
                
        except mysql.connector.Error as err:
            conn.rollback()
            flash(f'Error adding songs: {str(err)}', 'danger')
            print(f"Database error: {str(err)}")  # Debugging
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('get_playlist_songs', playlist_id=playlist_id))
    
    # Fetch all playlists for the user
    cursor.execute('SELECT id, name, song_count, created_at FROM playlists WHERE user_id = %s', (session['user_id'],))
    playlists = cursor.fetchall()
    
    # Fetch all songs
    cursor.execute('SELECT id, title, artist FROM songs')
    songs = cursor.fetchall()
    
    # Fetch existing song IDs in the playlist
    cursor.execute('SELECT song_id FROM playlist_songs WHERE playlist_id = %s', (playlist_id,))
    existing_song_ids = {row['song_id'] for row in cursor.fetchall()}
    
    cursor.close()
    conn.close()
    
    return render_template('playlists.html', 
                         username=session.get('username', 'User'), 
                         playlists=playlists, 
                         songs=songs, 
                         playlist_id=playlist_id, 
                         existing_song_ids=existing_song_ids, 
                         active_page='playlists')

# Existing routes provided by the user
@app.route('/get_playlist_songs/<int:playlist_id>')
@login_required
def get_playlist_songs(playlist_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify playlist exists and belongs to the user
    cursor.execute('SELECT name FROM playlists WHERE id = %s AND user_id = %s', (playlist_id, session['user_id']))
    playlist = cursor.fetchone()
    
    if not playlist:
        flash('Playlist not found or unauthorized', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('playlists'))
    
    # Fetch songs in the playlist
    cursor.execute('''
        SELECT s.id, s.title, s.artist, s.url 
        FROM songs s 
        JOIN playlist_songs ps ON s.id = ps.song_id 
        WHERE ps.playlist_id = %s
    ''', (playlist_id,))
    songs = cursor.fetchall()
    
    # Fetch all songs for the add modal
    cursor.execute('SELECT id, title, artist FROM songs')
    all_songs = cursor.fetchall()
    
    # Fetch existing song IDs in the playlist
    cursor.execute('SELECT song_id FROM playlist_songs WHERE playlist_id = %s', (playlist_id,))
    existing_song_ids = {row['song_id'] for row in cursor.fetchall()}
    
    cursor.close()
    conn.close()
    
    return render_template('playlist_songs.html', 
                         username=session.get('username', 'User'), 
                         songs=songs, 
                         all_songs=all_songs, 
                         existing_song_ids=existing_song_ids, 
                         playlist_name=playlist['name'], 
                         playlist_id=playlist_id, 
                         active_page='playlists')

@app.route('/delete_playlist/<int:playlist_id>', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM playlist_songs WHERE playlist_id = %s AND EXISTS (SELECT 1 FROM playlists WHERE id = %s AND user_id = %s)', 
                      (playlist_id, playlist_id, session['user_id']))
        cursor.execute('DELETE FROM playlists WHERE id = %s AND user_id = %s', (playlist_id, session['user_id']))
        conn.commit()
        flash('Playlist deleted successfully', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error deleting playlist: {str(err)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('playlists'))

# New route to delete a song from a playlist
@app.route('/delete_playlist_song/<int:playlist_id>/<int:song_id>', methods=['POST'])
@login_required
def delete_playlist_song(playlist_id, song_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verify playlist belongs to the user
        cursor.execute('SELECT id FROM playlists WHERE id = %s AND user_id = %s', (playlist_id, session['user_id']))
        playlist = cursor.fetchone()
        if not playlist:
            flash('Playlist not found or unauthorized', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('playlists'))
        
        # Delete the song from the playlist
        cursor.execute('DELETE FROM playlist_songs WHERE playlist_id = %s AND song_id = %s', (playlist_id, song_id))
        if cursor.rowcount > 0:
            conn.commit()
            flash('Song removed from playlist successfully', 'success')
        else:
            flash('Song not found in playlist', 'danger')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error removing song: {str(err)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('get_playlist_songs', playlist_id=playlist_id))

@app.route('/history')
@login_required
def history():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT id, mood, playedsong, song_artist, song_url, day_date 
        FROM history 
        WHERE user_id = %s 
        ORDER BY day_date DESC
    ''', (session['user_id'],))
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('history.html', username=session['username'], history=history, active_page='history')

# New route to delete a history entry
@app.route('/delete_history/<int:history_id>', methods=['POST'])
@login_required
def delete_history(history_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verify history entry belongs to the user
        cursor.execute('SELECT id FROM history WHERE id = %s AND user_id = %s', (history_id, session['user_id']))
        history_entry = cursor.fetchone()
        if not history_entry:
            flash('History entry not found or unauthorized', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('history'))
        
        # Delete the history entry
        cursor.execute('DELETE FROM history WHERE id = %s AND user_id = %s', (history_id, session['user_id']))
        if cursor.rowcount > 0:
            conn.commit()
            flash('History entry deleted successfully', 'success')
        else:
            flash('History entry not found', 'danger')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error deleting history entry: {str(err)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('history'))

@app.route('/logout')
@login_required
def logout():
    session.clear()
    response = redirect(url_for('login'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    flash('You have been logged out', 'success')
    return response

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password and password != confirm_password:
            flash('Passwords do not match', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('settings'))
        
        try:
            updates = []
            params = []
            
            if username and username != session['username']:
                cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (username, session['user_id']))
                if cursor.fetchone():
                    flash('Username already exists', 'danger')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('settings'))
                updates.append('username = %s')
                params.append(username)
                session['username'] = username
            
            if email:
                cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, session['user_id']))
                if cursor.fetchone():
                    flash('Email already registered', 'danger')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('settings'))
                updates.append('email = %s')
                params.append(email)
            
            if password:
                updates.append('password_hash = %s')
                params.append(generate_password_hash(password))
            
            if updates:
                params.append(session['user_id'])
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, params)
                conn.commit()
                flash('Settings updated successfully', 'success')
            else:
                flash('No changes made', 'info')
                
        except mysql.connector.Error as err:
            conn.rollback()
            flash(f'Error updating settings: {str(err)}', 'danger')
        
        cursor.close()
        conn.close()
        return redirect(url_for('settings'))
    
    cursor.execute('SELECT username, email FROM users WHERE id = %s', (session['user_id'],))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('settings.html', username=session['username'], user_data=user_data, active_page='settings')

# Admin Routes
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM admins WHERE admin_username = %s', (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if admin and check_password_hash(admin['admin_password'], password):
            session['admin_id'] = admin['admin_id']
            session['admin_name'] = admin['admin_name']
            session['admin_username'] = admin['admin_username']
            flash('Login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'danger')
        return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/adminDashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT COUNT(*) as count FROM users')
    total_users = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM songs')
    total_songs = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM playlists')
    total_playlists = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return render_template('adminDashboard.html', 
                         admin=session,
                         total_users=total_users,
                         total_songs=total_songs,
                         total_playlists=total_playlists)

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, username, email, created_at, email_notifications, explicit_content FROM users')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin_users.html', admin=session, users=users)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM playlists WHERE user_id = %s', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        flash('User deleted successfully', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error deleting user: {str(err)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        admin_name = request.form.get('admin_name')
        admin_username = request.form.get('admin_username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password and password != confirm_password:
            flash('Passwords do not match', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('admin_settings'))
        
        try:
            updates = []
            params = []
            
            if admin_name:
                updates.append('admin_name = %s')
                params.append(admin_name)
                session['admin_name'] = admin_name
                
            if admin_username:
                updates.append('admin_username = %s')
                params.append(admin_username)
                session['admin_username'] = admin_username
                
            if password:
                updates.append('admin_password = %s')
                params.append(generate_password_hash(password))
                
            if updates:
                params.append(session['admin_id'])
                query = f"UPDATE admins SET {', '.join(updates)} WHERE admin_id = %s"
                cursor.execute(query, params)
                conn.commit()
                flash('Settings updated successfully', 'success')
            else:
                flash('No changes made', 'info')
                
        except mysql.connector.Error as err:
            conn.rollback()
            flash(f'Error updating settings: {str(err)}', 'danger')
        
        cursor.close()
        conn.close()
        return redirect(url_for('admin_settings'))
    
    cursor.execute('SELECT admin_name, admin_username FROM admins WHERE admin_id = %s', (session['admin_id'],))
    admin_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('admin_settings.html', admin=session, admin_data=admin_data)

@app.route('/admin_logout')
@admin_required
def admin_logout():
    session.clear()
    response = redirect(url_for('admin_login'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    flash('You have been logged out', 'success')
    return response

# Mood Detection Functions
def detect_emotion_from_image(image_path):
    try:
        image = cv2.imread(image_path)
        if image is None:
            return 'neutral'
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = emotion_detector.detect_emotions(image_rgb)
        if not results:
            return 'neutral'
        emotions = results[0]['emotions']
        return max(emotions.items(), key=lambda x: x[1])[0]
    except Exception as e:
        print(f"Error detecting emotion: {e}")
        return 'neutral'

def detect_emotion_from_text(text):
    lower_text = text.lower()
    mood_keywords = ['happy', 'relaxed', 'neutral', 'sad', 'angry']
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
        else:
            return 'angry'
    except Exception as e:
        print(f"Error analyzing text: {e}")
        return 'neutral'

# Mood Detection Routes
@app.route('/detect/face', methods=['POST'])
def detect_face_emotion():
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image provided', 'error_code': 400}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file', 'error_code': 400}), 400
    
    try:
        filename = secure_filename(f"face_{int(time.time())}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        emotion = detect_emotion_from_image(filepath)
        query = MOOD_QUERIES.get(emotion, MOOD_QUERIES['neutral'])['query']
        videos = youtube_music.search_videos(query)
        
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
    text = request.form.get('text', '').strip()
    if not text or len(text) < 3:
        return jsonify({'status': 'error', 'message': 'Please enter at least 3 characters', 'error_code': 400}), 400
    
    try:
        emotion = detect_emotion_from_text(text)
        query = MOOD_QUERIES.get(emotion, MOOD_QUERIES['neutral'])['query']
        videos = youtube_music.search_videos(query)
        
        return jsonify({
            'status': 'success',
            'emotion': emotion,
            'tracks': videos,
            'query': query,
            'count': len(videos)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to analyze text',
            'error': str(e),
            'error_code': 500
        }), 500

@app.route('/detect/image', methods=['POST'])
def detect_image_emotion():
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image provided', 'error_code': 400}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file', 'error_code': 400}), 400
    
    try:
        filename = secure_filename(f"img_{int(time.time())}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        emotion = detect_emotion_from_image(filepath)
        query = MOOD_QUERIES.get(emotion, MOOD_QUERIES['neutral'])['query']
        videos = youtube_music.search_videos(query)
        
        return jsonify({
            'status': 'success',
            'emotion': emotion,
            'tracks': videos,
            'image_url': url_for('static', filename=f'uploads/{filename}'),
            'query': query,
            'count': len(videos)
        })
    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            'status': 'error',
            'message': 'Failed to process image',
            'error': str(e),
            'error_code': 500
        }), 500

@app.route('/record-played-song', methods=['POST'])
@login_required
def record_played_song():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        mood = data.get('mood')
        song_title = data.get('song_title')
        artist = data.get('artist', 'Unknown Artist')
        url = data.get('url', '')
        
        if not mood or not song_title:
            return jsonify({'success': False, 'error': 'Mood and song title are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO history 
                (user_id, mood, playedsong, song_artist, song_url, day_date)
            VALUES 
                (%s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(query, (session['user_id'], mood, song_title, artist, url))
        conn.commit()
        
        history_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'history_id': history_id})
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to record song in history'
        }), 500

if __name__ == '__main__':
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/img', exist_ok=True)
    app.run(debug=True)
