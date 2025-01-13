# from flask import Flask, render_template, request, jsonify
# import pickle
# import asyncio
# from youtubesearchpython.__future__ import VideosSearch
# from yt_dlp import YoutubeDL
# from recommender import get_metadata, hybrid_recommend

# app = Flask(__name__)

# # Load data
# data = pickle.load(open("pickles/data.pkl", "rb"))


# @app.route("/")
# def index():
#     """Render the main page."""
#     tracks = data["track_name"].tolist()
#     return render_template("index.html", tracks=tracks)


# async def fetch_youtube_data_async(song):
#     """Fetch YouTube video details asynchronously for a given song."""
#     search_query = f"{song['track_name']} {song['track_artist']}"
#     video_search = VideosSearch(search_query, limit=1)
#     result = await video_search.next()

#     for video in result.get("result", []):
#         if not video.get("isLive", False) and video.get("id"):
#             audio_url = fetch_audio_url(video.get("id"))
#             return {
#                 "thumbnail": video.get("thumbnails", [{}])[0].get("url", ""),
#                 "video_id": video.get("id", ""),
#                 "audio_url": audio_url,
#                 "embeddable": True,
#             }
#     return {"thumbnail": "", "video_id": "", "audio_url": None, "embeddable": False}


# def fetch_audio_url(video_id):
#     """Fetch the audio URL using yt-dlp."""
#     ydl_opts = {"format": "bestaudio/best", "quiet": True}
#     with YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(
#             f"https://www.youtube.com/watch?v={video_id}", download=False
#         )
#         return info.get("url")


# @app.route("/recommend", methods=["POST"])
# async def recommend():
#     """Handle AJAX request for song recommendations."""
#     selected_song = request.form.get("song", "").strip()
#     discovery_mode = request.form.get("discovery_mode", "popular")
#     count = int(request.form.get("count", 2))  # Set lower count for faster response

#     # Find the song index
#     matches = data[data["track_name"].str.lower() == selected_song.lower()]
#     if matches.empty:
#         return jsonify({"error": f"No song found with the name '{selected_song}'"}), 404

#     selected_index = matches.index[0]
#     recommendations = hybrid_recommend(selected_index, count)

#     # Fetch YouTube data asynchronously
#     tasks = [
#         fetch_youtube_data_async(song)
#         for rec_type, songs in recommendations.items()
#         for song in songs
#     ]
#     youtube_data = await asyncio.gather(*tasks)

#     # Map YouTube data back to recommendations
#     index = 0
#     for rec_type, songs in recommendations.items():
#         for song in songs:
#             song.update(youtube_data[index])
#             index += 1

#     # Fetch current song data
#     current_song = get_metadata(selected_index)
#     current_video = await fetch_youtube_data_async(current_song)

#     return jsonify({"current_video": current_video, "recommendations": recommendations})


# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, render_template, request, jsonify, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import os
import pickle
import asyncio
from youtubesearchpython.__future__ import VideosSearch
from yt_dlp import YoutubeDL
from recommender import get_metadata, hybrid_recommend

app = Flask(__name__)
app.secret_key = os.urandom(24)
bcrypt = Bcrypt(app)

# MongoDB Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["music_recommendation"]
users_collection = db["users"]

# Load data
data = pickle.load(open("pickles/data.pkl", "rb"))


# Helper Functions
def is_logged_in():
    return "user" in session


@app.route("/")
def index():
    if is_logged_in():
        return render_template(
            "index.html", user=session["user"], tracks=data["track_name"].tolist()
        )
    return render_template("auth.html")


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    users_collection.insert_one(
        {
            "username": username,
            "password": hashed_password,
            "playlists": {},
            "history": [],
        }
    )
    return jsonify({"message": "Registration successful"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = users_collection.find_one({"username": username})
    if user and bcrypt.check_password_hash(user["password"], password):
        session["user"] = username
        return jsonify({"message": "Login successful", "redirect": "/"}), 200

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/profile", methods=["GET"])
def profile():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    user = users_collection.find_one({"username": session["user"]})
    if user:
        return jsonify(
            {
                "username": user["username"],
                "playlists": user.get("playlists", {}),
                "history": user.get("history", []),
            }
        )
    return jsonify({"error": "User not found"}), 404


@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    playlist_name = data.get("playlist_name")

    if not playlist_name:
        return jsonify({"error": "Playlist name is required"}), 400

    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"error": "User not found"}), 404

    playlists = user.get("playlists", {})
    if playlist_name in playlists:
        return jsonify({"error": "Playlist already exists"}), 400

    playlists[playlist_name] = []
    users_collection.update_one(
        {"username": session["user"]}, {"$set": {"playlists": playlists}}
    )
    return jsonify({"message": "Playlist created successfully"}), 201


@app.route("/add_to_playlist", methods=["POST"])
def add_to_playlist():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    playlist_name = data.get("playlist_name")
    track = data.get("track")

    if not playlist_name or not track:
        return jsonify({"error": "Playlist name and track are required"}), 400

    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"error": "User not found"}), 404

    playlists = user.get("playlists", {})
    if playlist_name not in playlists:
        playlists[playlist_name] = []

    if track not in playlists[playlist_name]:  # Avoid duplicates
        playlists[playlist_name].append(track)
        users_collection.update_one(
            {"username": session["user"]}, {"$set": {"playlists": playlists}}
        )
        return jsonify({"message": "Track added to playlist"}), 200
    return jsonify({"message": "Track already in playlist"}), 200


@app.route("/remove_from_playlist", methods=["POST"])
def remove_from_playlist():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    playlist_name = data.get("playlist_name")
    track = data.get("track")

    if not playlist_name or not track:
        return jsonify({"error": "Playlist name and track are required"}), 400

    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"error": "User not found"}), 404

    playlists = user.get("playlists", {})
    if playlist_name in playlists and track in playlists[playlist_name]:
        playlists[playlist_name].remove(track)
        users_collection.update_one(
            {"username": session["user"]}, {"$set": {"playlists": playlists}}
        )
        return jsonify({"message": "Track removed from playlist"}), 200
    return jsonify({"error": "Track not found in playlist"}), 404


@app.route("/add_to_history", methods=["POST"])
def add_to_history():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    track = data.get("track")

    if not track:
        return jsonify({"error": "Track is required"}), 400

    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"error": "User not found"}), 404

    history = user.get("history", [])
    if track not in history:  # Avoid duplicates
        history.insert(0, track)  # Add to beginning of history
        if len(history) > 50:  # Limit history to 50 songs
            history.pop()

    users_collection.update_one(
        {"username": session["user"]}, {"$set": {"history": history}}
    )
    return jsonify({"message": "History updated successfully"}), 200


@app.route("/clear_history", methods=["POST"])
def clear_history():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    users_collection.update_one(
        {"username": session["user"]}, {"$set": {"history": []}}
    )
    return jsonify({"message": "History cleared successfully"}), 200


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/recommend", methods=["POST"])
async def recommend():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        selected_song = request.form.get("song", "").strip()
        discovery_mode = request.form.get("discovery_mode", "popular")
        count = int(request.form.get("count", 2))

        # Get user's history
        user = users_collection.find_one({"username": session["user"]})
        history = user.get("history", []) if user else []

        # Find the song index
        matches = data[data["track_name"].str.lower() == selected_song.lower()]
        if matches.empty:
            return (
                jsonify({"error": f"No song found with the name '{selected_song}'"}),
                404,
            )

        selected_index = matches.index[0]

        # Get base recommendations for the selected song
        base_recommendations = hybrid_recommend(selected_index, count)

        # Initialize combined recommendations with base recommendations
        combined_recommendations = base_recommendations.copy()

        # Get additional recommendations based on user's history (last 3 songs)
        if history:
            history_recommendations = {}
            for history_song in history[:3]:  # Consider last 3 played songs
                history_matches = data[
                    data["track_name"].str.lower() == history_song.lower()
                ]
                if not history_matches.empty:
                    history_index = history_matches.index[0]
                    history_recs = hybrid_recommend(history_index, max(1, count // 2))

                    if history_recs:  # Only process if we got recommendations
                        # Merge recommendations from history
                        for rec_type, songs in history_recs.items():
                            if rec_type not in history_recommendations:
                                history_recommendations[rec_type] = []
                            history_recommendations[rec_type].extend(songs)

            # Merge history recommendations into combined recommendations
            for rec_type, songs in history_recommendations.items():
                if rec_type in combined_recommendations:
                    # Add unique songs from history recommendations
                    existing_names = {
                        song["track_name"]
                        for song in combined_recommendations[rec_type]
                    }
                    new_songs = [
                        song
                        for song in songs
                        if song["track_name"] not in existing_names
                    ]
                    combined_recommendations[rec_type].extend(new_songs[:count])
                else:
                    combined_recommendations[rec_type] = songs[:count]

        # Filter out songs from history
        filtered_recommendations = {
            key: [song for song in songs if song["track_name"] not in history]
            for key, songs in combined_recommendations.items()
        }

        # Remove empty categories and limit to count
        filtered_recommendations = {
            key: songs[:count]
            for key, songs in filtered_recommendations.items()
            if songs
        }

        if not filtered_recommendations:
            # If no recommendations after filtering, get new ones ignoring history
            base_recommendations = hybrid_recommend(selected_index, count + 3)
            filtered_recommendations = {
                key: songs[:count] for key, songs in base_recommendations.items()
            }

        # Fetch YouTube data asynchronously
        tasks = [
            fetch_youtube_data_async(song)
            for rec_type, songs in filtered_recommendations.items()
            for song in songs
        ]
        youtube_data = await asyncio.gather(*tasks)

        # Map YouTube data back to recommendations
        index = 0
        for rec_type, songs in filtered_recommendations.items():
            for song in songs:
                song.update(youtube_data[index])
                index += 1

        # Fetch current song data
        current_song = get_metadata(selected_index)
        current_video = await fetch_youtube_data_async(current_song)

        return jsonify(
            {
                "current_video": current_video,
                "recommendations": filtered_recommendations,
            }
        )

    except Exception as e:
        print(f"Error in recommend route: {e}")
        return (
            jsonify(
                {
                    "error": "An error occurred while getting recommendations. Please try again."
                }
            ),
            500,
        )


async def fetch_youtube_data_async(song):
    """Fetch YouTube video details asynchronously for a given song."""
    search_query = f"{song['track_name']} {song['track_artist']}"
    video_search = VideosSearch(search_query, limit=1)
    result = await video_search.next()

    for video in result.get("result", []):
        if not video.get("isLive", False) and video.get("id"):
            audio_url = fetch_audio_url(video.get("id"))
            return {
                "thumbnail": video.get("thumbnails", [{}])[0].get("url", ""),
                "video_id": video.get("id", ""),
                "audio_url": audio_url,
                "embeddable": True,
                "track_name": song.get("track_name", ""),
                "track_artist": song.get("track_artist", ""),
            }
    return {
        "thumbnail": "",
        "video_id": "",
        "audio_url": None,
        "embeddable": False,
        "track_name": song.get("track_name", ""),
        "track_artist": song.get("track_artist", ""),
    }


def fetch_audio_url(video_id):
    """Fetch the audio URL using yt-dlp."""
    ydl_opts = {"format": "bestaudio/best", "quiet": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}", download=False
        )
        return info.get("url")


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
