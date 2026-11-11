import os, requests, time
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, session, url_for, redirect, request

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY")

# os.urandom(64)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"

# PERMISSIONS
SCOPE = 'playlist-read-private user-read-private user-library-read'

# CACHE IN SESSION
CACHE_HANDLER = FlaskSessionCacheHandler(session)

# RECCOBEATS CACHE
RECCOBEATS_BASE = "https://api.reccobeats.com/v1"
reccobeats_cache = {}

# AUDIO FEATURES
AUDIO_KEYS = ['acousticness', 'danceability', 'energy', 'instrumentalness',
              'liveness', 'loudness', 'speechiness', 'tempo', 'valence']

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_handler=CACHE_HANDLER,
    show_dialog=True
)

sp = Spotify(auth_manager=sp_oauth)


def spotify_login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not sp_oauth.validate_token(CACHE_HANDLER.get_cached_token()):
            return redirect(sp_oauth.get_authorize_url())
        return view(*args, **kwargs)

    return wrapped_view


# ENDPOINTS
# app = FLASK APP
# route = DEFINE ROUTE
@app.route('/')
@spotify_login_required
def home():
    return redirect(url_for('get_playlists'))

@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_playlists'))

# GET USER PLAYLISTS
@app.route('/get_playlists')
@spotify_login_required
def get_playlists():
    playlists = sp.current_user_playlists()
    playlists_info = [
        (pl.get('id'), pl.get('name'), pl.get('tracks', {}).get('total'))
        for pl in playlists.get('items', [])
    ]
    links = [
        f'<a href="{url_for("get_tracks", playlist_id=pid)}">{name}</a> ({total} tracks)'
        for pid, name, total in playlists_info
        if pid and name
    ]
    playlists_display = '<br>'.join(links) if links else '<p>No playlists found.</p>'
    return f'<html><body><h1>Your Playlists</h1>{playlists_display}</body></html>'


# GET PLAYLIST TRACKS
@app.route('/tracks/<playlist_id>')
@spotify_login_required
def get_tracks(playlist_id):
    tracks = []
    results = sp.playlist_items(playlist_id, additional_types=['track'])
  
    while results:
        for item in results['items']:
            track = item.get('item')
            if not track:
                continue  # local files or removed tracks can come back as None
            tracks.append({
                'id': track['id'],
                'name': track['name'],
                'artists': [(a['name'], a['id']) for a in track['artists']],
            })
        results = sp.next(results) if results.get('next') else None
    return tracks

    # rows = '<br>'.join(
    #     f"{t['name']} — {', '.join(a[0] for a in t['artists'])}"
    #     for t in tracks
    # )
    # return f'<html><body><h1>{len(tracks)} tracks</h1>{rows}</body></html>'

# BUILD DATASET WITH DATA FEATURES
def build_dataset(playlist_id, limit=None):
    tracks = get_tracks(playlist_id)
    if limit:
        tracks = tracks[:limit]

    dataset = []
    for t in tracks:
        # genres = sorted({g for _, aid in t['artists'] for g in get_artist_genres(aid)})
        features = get_audio_features_reccobeats(t['id'])
        audio = {k: features.get(k) for k in AUDIO_KEYS} if features else None
        dataset.append({
            'id': t['id'],
            'name': t['name'],
            'artists': [name for name, _ in t['artists']],
            # 'genres': genres,
            'audio': audio,
        })
        time.sleep(0.2)  # be polite to both APIs
    return dataset

# TEST
def get_audio_features_reccobeats(spotify_track_id):
    if spotify_track_id in reccobeats_cache:
        return reccobeats_cache[spotify_track_id]

    features = None
    try:
        resolve_resp = requests.get(f"{RECCOBEATS_BASE}/track", params={"ids": spotify_track_id}, timeout=10)
        resolve_resp.raise_for_status()
        content = resolve_resp.json().get("content", [])
        if content:
            recco_id = content[0]["id"]
            feat_resp = requests.get(f"{RECCOBEATS_BASE}/track/{recco_id}/audio-features", timeout=10)
            if feat_resp.status_code == 200:
                features = feat_resp.json()
    except requests.RequestException as e:
        print(f"ReccoBeats lookup failed for {spotify_track_id}: {e}")

    reccobeats_cache[spotify_track_id] = features
    return features

# PLAYLIST COVERAGE REPORT
@app.route('/dataset/<playlist_id>')
def dataset_summary(playlist_id):
    if not sp_oauth.validate_token(CACHE_HANDLER.get_cached_token()):
        return redirect(sp_oauth.get_authorize_url())

    limit = request.args.get('limit', type=int)
    data = build_dataset(playlist_id, limit=limit)

    total = len(data)
    with_audio = sum(1 for d in data if d['audio'])
    # with_genres = sum(1 for d in data if d['genres'])
    # with_both = sum(1 for d in data if d['audio'] and d['genres'])
    # with_neither = sum(1 for d in data if not d['audio'] and not d['genres'])

    return (
        f"<pre>Tracks: {total}\n"
        f"With audio features: {with_audio}\n"
        # f"With genres: {with_genres}\n"
        # f"With both: {with_both}\n"
        # f"With neither: {with_neither}</pre>"
    )

    

@app.route('/test_reccobeats/<spotify_track_id>')
def test_reccobeats(spotify_track_id):
    import requests
    resp = requests.get(
        "https://api.reccobeats.com/v1/track",
        params={"ids": spotify_track_id}
    )

    features_test = get_audio_features_reccobeats(spotify_track_id)
    return f"<pre>{features_test}</pre>"




@app.route('/logout')
def logout():
     session.clear()
     return redirect(url_for('home'))
    

# FLASK SESSION
if __name__ == '__main__':
    app.run(debug=True)