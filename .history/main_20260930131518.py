import os 
import sys
from dotenv import load_dotenv
from flask import Flask, session, url_for, redirect
from pathlib import Path

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

# Load .env from project directory if present
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: Missing Spotify credentials.")
    print(f"CLIENT_ID set: {bool(CLIENT_ID)}, CLIENT_SECRET set: {bool(CLIENT_SECRET)}")
    print(f"Looking for .env at: {env_path}")
    print("Create a .env file with CLIENT_ID and CLIENT_SECRET, or set them in the environment.")
    sys.exit(1)

# PERMISSIONS
SCOPE = 'playlist-read-private'

# CACHE IN SESSION
CACHE_HANDLER = FlaskSessionCacheHandler(session)

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_handler=CACHE_HANDLER,
    show_dialog=True
)

sp = Spotify(auth_manager=sp_oauth)

# ENDPOINTS
# app = FLASK APP
# route = DEFINE ROUTE
@app.route('/')
def home():
    if not sp_oauth.validate_token(CACHE_HANDLER.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))

# FLASK SESSION
if __name__ == '__main__':
    app.run(debug=True)