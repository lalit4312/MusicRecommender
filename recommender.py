import pickle
import pandas as pd
import numpy as np

data = pickle.load(open("pickles/data.pkl", "rb"))
lyric_similarity_mapping = pickle.load(
    open("pickles/lyric_similarity_mapping.pkl", "rb")
)
energy_similarity_mapping = pickle.load(
    open("pickles/energy_similarity_mapping.pkl", "rb")
)
mood_similarity_mapping = pickle.load(open("pickles/mood_similarity_mapping.pkl", "rb"))


def get_metadata(track_index):
    return data.iloc[track_index][["track_name", "track_artist", "lyrics"]].to_dict()


def recommend_similar(track_index, similarity_mapping, count, prioritize_popular):
    similar_indices = np.argsort(similarity_mapping[track_index])[1 : count + 1]
    recommendations = data.iloc[similar_indices]
    return recommendations[["track_name", "track_artist"]].to_dict(orient="records")


def hybrid_recommend(track_index, count=5, prioritisePopular=True):
    return {
        "lyrically similar": recommend_similar(
            track_index, lyric_similarity_mapping, count, prioritisePopular
        ),
        "similar energy": recommend_similar(
            track_index, energy_similarity_mapping, count, prioritisePopular
        ),
        "similar mood": recommend_similar(
            track_index, mood_similarity_mapping, count, prioritisePopular
        ),
    }
