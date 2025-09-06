# MoodBeats - Music Recommendation Web App

MoodBeats is a Flask-based web application that allows users to explore songs by mood, manage favorite songs, create playlists, track mood history, and search for YouTube songs. The app features a modern dashboard with a sidebar, song playback in modals, and a responsive design using Bootstrap and Font Awesome.

## Prerequisites

- **Python**: Version 3.8 or higher
- **MySQL**: Installed and running (e.g., via XAMPP, WAMP, or standalone)
- **phpMyAdmin**: For database import (optional)
- **pip**: Python package manager
- **Web Browser**: Chrome, Firefox, or any modern browser

## Setup Instructions



### Step 1: Import the Database
1. **Download the Database**:
   - Locate the `moodbeats.db` file (or `moodbeats.sql` if provided) in the project repository or generate it from the database schema.

2. **Import Using phpMyAdmin**:
   - Open phpMyAdmin in your browser (e.g., `http://localhost/phpmyadmin` if using XAMPP).
   - Create a new database named `moodbeats`.
   - Go to the "Import" tab, select the `moodbeats.sql` file, and click "Go" to import the database.
   - Alternatively, use the MySQL command line:
     ```bash
     mysql -u root -p moodbeats < moodbeats.sql
     ```
     Replace `root` with your MySQL username and enter your password when prompted.

3. **Update Database Configuration**:
   - Modify the `db_config` dictionary to match your MySQL credentials:
     ```python
     # Database configuration
     db_config = {
         'host': 'localhost',
         'user': 'root',              # Your MySQL username
         'password': 'your_password', # Your MySQL password
         'database': 'moodbeats'      # Database name
     }
     ```
   - Save the file.



### Step 2: Install Python Dependencies
1. **Install Required Libraries**:
   - The project requires several Python libraries listed in `requirements.txt`. Install them using:
     ```bash
     pip install -r requirements.txt
     ```
   - If `requirements.txt` is not provided, install the following libraries manually:
     ```bash
     pip install flask flask-login mysql-connector-python python-dotenv requests
     ```
   - **Libraries Used**:
     - `flask`: Web framework
     - `flask-login`: User session management
     - `mysql-connector-python`: MySQL database connector
     - `python-dotenv`: Environment variable management (optional)
     - `requests`: For API calls (e.g., YouTube search)



### Step 3: Run the Application
1. **Start the Flask Server**:
   - In the terminal, navigate to the project directory and run:
     ```bash
     python app.py
     ```
     or
     ```bash
     python3 app.py
     ```
   - The app should start on `http://localhost:5000` (or another port if configured).

2. **Access the App**:
   - Open a web browser and go to `http://localhost:5000`.
   - Register a new account or log in with existing credentials to access the dashboard.




## Project Structure
```
moodbeats/
├── app.py                    # Main Flask application
├── templates/                # HTML templates
│   ├── dashboard.html        # User dashboard
│   ├── history.html          # Mood history page
│   ├── favorites.html        # Favorite songs page
│   ├── playlist_songs.html   # Playlist songs page
│   ├── loginhome.html        # Home page after login
├── static/                   # Static files
│   ├── img/
│       ├── logo.png          # App logo
├── moodbeats.sql             # Database schema
├── requirements.txt          # Python dependencies
├── README.md                 # This file
```

