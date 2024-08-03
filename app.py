from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import requests
from urllib.parse import urlencode
import base64

app = Flask(__name__)
app.secret_key = 'a_very_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

headings = ("Track", "Artist", "Album")
data = [
    ("Song", "Artist", "Album")
]

client_id = "938f5972b54041a88accf1dc19a89c89"
client_secret = "dcdfa4e507d948adb5a8a98f64a63e75"
redirect_uri = "http://localhost:7777/callback"


auth_params = {
    "client_id": client_id,
    "response_type": "code",
    "redirect_uri": redirect_uri,
    "scope": "user-top-read"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    print('login route')
    # direct user to authorization via Spotify
    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(auth_params)
    # Open the authorization URL in the browser
    return redirect(auth_url)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/display', methods=['POST'])
def display():
    choice = request.form.get('choice')
    print(f"User choice received: {choice}")

    if not choice:
        return "No choice selected."

    if 'access_token' not in session:
        return redirect(url_for('login'))

    token = session['access_token']

    if choice == 'top_songs':
        data = get_top_songs(token)
    elif choice == 'recommendations':
        data = get_recommendations(token)
    else:
        return "Invalid choice."

    return render_template("recs.html", headings=headings, data=data)

@app.route('/callback')
def callback():
    print("callback route accessed")
    if 'code' in request.args:
        code = request.args.get('code')
        print(f"Authorization code received: {code}")

          # Prepare token request
        token_endpoint = "https://accounts.spotify.com/api/token"
        encoded_credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode("utf-8")

        token_headers = {
        "Authorization": "Basic " + encoded_credentials,
        "Content-Type": "application/x-www-form-urlencoded"
        }

        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }

        # Request access token
        r = requests.post(token_endpoint, data=token_data, headers=token_headers)


        
        if r.status_code == 200:
            token = r.json().get("access_token")
            session['access_token'] = token

            # Call function to get top songs
            # top_tracks = get_top_songs(token)

            # if top_tracks is None:
            #     top_tracks = []


            return redirect(url_for('home'))

        else: 
            return "Error obtaining access token.", r.status_code, r.text
            # Here you can redirect to recs.html passing the authorization code
    else:
        print("No code parameter found in request")
        return "Authorization code not found in callback parameters."
    

def get_recommendations(token):
    rec_headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }

    rec_params = {
        "seed_artists": "your_seed_artists",
        "seed_genres": "your_seed_genres",
        "seed_tracks": "your_seed_tracks",
        "limit": 50
    }

    get_rec_response = requests.get("https://api.spotify.com/v1/recommendations", params=rec_params, headers=rec_headers)

    if get_rec_response.status_code == 200:
        rec_info = get_rec_response.json()
        recommendations = rec_info.get("tracks", [])
        return [(track.get("name"), track.get("artists")[0].get("name"), track.get("album").get("name")) for track in recommendations]
    else:
        print("Error fetching recommendations:", get_rec_response.status_code, get_rec_response.text)
        return []


#get user's recently played tracks
def get_top_songs(token):
    top_headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }

    top_params = {
        "type":"tracks",
        "time_range":"short_term",
        "limit": 50,
    }

    get_top_response = requests.get("https://api.spotify.com/v1/me/top/tracks", params=top_params, headers=top_headers)

    if get_top_response.status_code == 200:
        track_info = get_top_response.json()

        top_tracks = track_info.get("items", [])
        return [(track.get("name"), track.get("artists")[0].get("name"), track.get("album").get("name")) for track in top_tracks]
    else:
        print("Error fetching top tracks:", get_top_response.status_code, get_top_response.text)
        return []
            
if __name__ == "__main__":
    app.run(port=7777, debug=True)
