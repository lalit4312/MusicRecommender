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


# def recommend_similar(track_index, similarity_mapping, count, prioritize_popular):
#     similar_indices = np.argsort(similarity_mapping[track_index])[1 : count + 1]
#     recommendations = data.iloc[similar_indices]
#     return recommendations[["track_name", "track_artist"]].to_dict(orient="records")


# def hybrid_recommend(track_index, count=5, prioritisePopular=True):
#     return {
#         "lyrically similar": recommend_similar(
#             track_index, lyric_similarity_mapping, count, prioritisePopular
#         ),
#         "similar energy": recommend_similar(
#             track_index, energy_similarity_mapping, count, prioritisePopular
#         ),
#         "similar mood": recommend_similar(
#             track_index, mood_similarity_mapping, count, prioritisePopular
#         ),
#     }


def recommend_similar(track_index, similarity_mapping, count, prioritize_popular):
    """Get similar songs with similarity scores."""
    try:
        similar_indices = np.argsort(similarity_mapping[track_index])[1 : count + 1]

        # Check if we got any recommendations
        if len(similar_indices) == 0:
            return []

        recommendations = data.iloc[similar_indices]

        # Calculate similarity scores
        similarity_scores = 1 - similarity_mapping[track_index][similar_indices]

        # Normalize scores safely
        if len(similarity_scores) > 0:
            score_min = similarity_scores.min()
            score_max = similarity_scores.max()

            # Handle case where all scores are the same
            if score_max == score_min:
                normalized_scores = np.ones_like(similarity_scores)
            else:
                normalized_scores = (similarity_scores - score_min) / (
                    score_max - score_min
                )
        else:
            return []

        # Create recommendation list with metadata and similarity scores
        rec_list = []
        for idx, (_, row) in enumerate(recommendations.iterrows()):
            rec_dict = {
                "track_name": row["track_name"],
                "track_artist": row["track_artist"],
                "similarity_score": float(normalized_scores[idx]),
            }
            rec_list.append(rec_dict)

        return rec_list
    except Exception as e:
        print(f"Error in recommend_similar: {e}")
        return []


def hybrid_recommend(track_index, count=5, prioritize_popular=True):
    """Get hybrid recommendations including similarity scores."""
    try:
        recommendations = {
            "lyrically similar": recommend_similar(
                track_index, lyric_similarity_mapping, count, prioritize_popular
            ),
            "similar energy": recommend_similar(
                track_index, energy_similarity_mapping, count, prioritize_popular
            ),
            "similar mood": recommend_similar(
                track_index, mood_similarity_mapping, count, prioritize_popular
            ),
        }

        # Remove any empty recommendation lists
        return {k: v for k, v in recommendations.items() if v}
    except Exception as e:
        print(f"Error in hybrid_recommend: {e}")
        return {}
