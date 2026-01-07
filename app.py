from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.inference import load_model, load_inference_data, recommend_for_user
from src.cold_start_handler import ColdStartHandler

app = Flask(__name__)
CORS(app)

MODEL = None
FEATURE_COLS = None
RATINGS = None
MOVIES = None
USER_STATS = None
ITEM_STATS = None
USER_GENRE_PREFS = None
USER_ID_SET = None
COLD_START_HANDLER = None

def init_app():
    global MODEL, FEATURE_COLS, RATINGS, MOVIES, USER_STATS, ITEM_STATS
    global USER_GENRE_PREFS, USER_ID_SET, COLD_START_HANDLER
    try:
        MODEL, FEATURE_COLS = load_model("ranker_model.pkl")
        RATINGS, MOVIES, USER_STATS, ITEM_STATS, USER_GENRE_PREFS = load_inference_data()
        USER_ID_SET = set(USER_STATS['UserID'].unique())
        COLD_START_HANDLER = ColdStartHandler()
        print("✅ SERVICE READY")
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)

def recommend_existing_user(user_id, top_k=10):
    try:
        if user_id not in USER_ID_SET:
            return None, "User not found"

        recs_df = recommend_for_user(
            user_id,
            MODEL,
            FEATURE_COLS,
            RATINGS,
            MOVIES,
            USER_STATS,
            ITEM_STATS,
            USER_GENRE_PREFS,
            top_k=top_k
        )

        if recs_df is None or recs_df.empty:
            return None, "No recommendations available"

        results = []
        for _, row in recs_df.iterrows():
            ry = row["Release_Year"] if "Release_Year" in row.index else None
            release_year = int(ry) if pd.notna(ry) else "N/A"

            movie_info = MOVIES[MOVIES["MovieID"] == row["MovieID"]]
            genres = "Movie"
            if not movie_info.empty:
                genre_cols = [c for c in MOVIES.columns if c not in ["MovieID", "Title", "Release_Year"]]
                active = [g for g in genre_cols if movie_info[g].iloc[0] == 1]
                if active:
                    genres = "|".join(active)

            avg_rating = (
                round(float(row["item_avg_rating"]), 2)
                if "item_avg_rating" in row.index and pd.notna(row["item_avg_rating"])
                else 0.0
            )

            num_ratings = (
                int(row["item_rating_count"])
                if "item_rating_count" in row.index and pd.notna(row["item_rating_count"])
                else 0
            )

            results.append({
                "movie_id": int(row["MovieID"]),
                "title": row["Title"],
                "release_year": release_year,
                "genres": genres,
                "score": round(float(row["score"]), 4),
                "avg_rating": avg_rating,
                "num_ratings": num_ratings
            })

        return results, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": MODEL is not None,
        "num_users": len(USER_ID_SET)
    }), 200

@app.route("/recommend", methods=["POST"])
def recommend():
    start = time.time()
    data = request.get_json() or {}
    user_id = data.get("user_id")
    top_k = data.get("top_k", 10)

    if user_id is None:
        return jsonify({"error": "Missing user_id"}), 400

    recs, error = recommend_existing_user(user_id, top_k)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({
        "user_id": user_id,
        "recommendations": recs,
        "latency_ms": round((time.time() - start) * 1000, 2)
    }), 200

@app.route("/recommend/new-user", methods=["POST"])
def recommend_new_user():
    start = time.time()
    data = request.get_json() or {}
    demo = data.get("demographics")
    top_k = data.get("top_k", 10)

    if not demo:
        return jsonify({"error": "Missing demographics"}), 400

    try:
        recs_df = COLD_START_HANDLER.recommend(user_demographics=demo, top_k=top_k)
        if recs_df is None or recs_df.empty:
            return jsonify({"error": "No recommendations generated"}), 500

        results = []
        for _, row in recs_df.iterrows():
            ry = row["Release_Year"] if "Release_Year" in row.index else None
            release_year = int(ry) if pd.notna(ry) else "N/A"

            avg_rating = (
                round(float(row["item_avg_rating"]), 2)
                if "item_avg_rating" in row.index and pd.notna(row["item_avg_rating"])
                else 0.0
            )

            num_ratings = (
                int(row["item_rating_count"])
                if "item_rating_count" in row.index and pd.notna(row["item_rating_count"])
                else 0
            )

            results.append({
                "title": row["Title"],
                "release_year": release_year,
                "genres": str(row["Genres"]) if "Genres" in row.index else "Movie",
                "avg_rating": avg_rating,
                "num_ratings": num_ratings
            })

        return jsonify({
            "recommendations": results,
            "latency_ms": round((time.time() - start) * 1000, 2)
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
