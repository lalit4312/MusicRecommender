import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

# Load and preprocess data
data = pd.read_csv("spotify_songs.csv")

# Filter English songs and drop unnecessary columns
data = data[data["language"] == "en"]
data.drop(columns=["language", "playlist_name", "playlist_id"], inplace=True)

# Drop duplicates
data = data.drop_duplicates(subset=["track_name", "track_artist"])

# Handle inconsistent date formats
# Convert to datetime, coercing errors to NaT, and fill missing values with "1900-01-01"
data["track_album_release_date"] = pd.to_datetime(
    data["track_album_release_date"], errors="coerce", format="mixed"
)
data["track_album_release_date"].fillna(pd.Timestamp("1900-01-01"), inplace=True)

# Sort data by release date and reset index
data = data.sort_values(by=["track_album_release_date"])
data.reset_index(drop=True, inplace=True)

# Separate features for recommendation
lyrics_data = data["lyrics"]
energy_data = data[["danceability", "tempo", "acousticness"]]
mood_data = data[["mode", "key", "valence"]]

# Compute similarity matrices
lyric_similarity_matrix = cosine_similarity(
    TfidfVectorizer(stop_words="english").fit_transform(lyrics_data)
)
energy_similarity_matrix = euclidean_distances(energy_data)
mood_similarity_matrix = euclidean_distances(mood_data)

# Save data and similarity mappings as pickle files
pickle.dump(data, open("pickles/data.pkl", "wb"))
pickle.dump(lyric_similarity_matrix, open("pickles/lyric_similarity_mapping.pkl", "wb"))
pickle.dump(
    energy_similarity_matrix, open("pickles/energy_similarity_mapping.pkl", "wb")
)
pickle.dump(mood_similarity_matrix, open("pickles/mood_similarity_mapping.pkl", "wb"))

print("Preprocessing complete.")
