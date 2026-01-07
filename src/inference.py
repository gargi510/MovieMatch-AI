import pandas as pd
import numpy as np
import pickle
import os

MODEL_DIR = "models"
PROCESSED_DIR = "data/processed"

def load_model(model_name="ranker_model.pkl"):
    with open(os.path.join(MODEL_DIR, model_name), "rb") as f:
        model = pickle.load(f)
    feature_cols = pd.read_csv(os.path.join(MODEL_DIR, "feature_names.csv"))["feature"].tolist()
    return model, feature_cols

def load_inference_data():
    ratings = pd.read_csv(os.path.join(PROCESSED_DIR, "ratings_processed.csv"))
    movies = pd.read_csv(os.path.join(PROCESSED_DIR, "movies_processed.csv"))
    user_stats = pd.read_csv(os.path.join(PROCESSED_DIR, "user_stats.csv"))
    item_stats = pd.read_csv(os.path.join(PROCESSED_DIR, "item_stats.csv"))
    user_genre_prefs = pd.read_csv(os.path.join(PROCESSED_DIR, "user_genre_preferences.csv"))
    return ratings, movies, user_stats, item_stats, user_genre_prefs

def generate_candidates_for_user(user_id, ratings, movies, item_stats, user_genre_prefs, n_candidates=200):
    user_history = set(ratings[ratings['UserID'] == user_id]['MovieID'])
    
    # Popular candidates
    popular = item_stats.nlargest(100, 'item_rating_count')['MovieID'].tolist()
    
    # Genre-based candidates
    genre_cols = [c for c in movies.columns if c not in ["MovieID", "Title", "Release_Year"]]
    user_prefs = user_genre_prefs[user_genre_prefs['UserID'] == user_id]
    
    genre_candidates = []
    if not user_prefs.empty:
        user_pref_cols = [c for c in user_prefs.columns if c.startswith("user_pref_")]
        genre_profile = user_prefs[user_pref_cols].values[0]
        
        movies_temp = movies.copy()
        movies_temp['genre_score'] = movies_temp[genre_cols].dot(genre_profile)
        genre_candidates = (
            movies_temp[~movies_temp['MovieID'].isin(user_history)]
            .nlargest(150, 'genre_score')['MovieID'].tolist()
        )
    
    # Combine and filter
    candidates = list(set(popular + genre_candidates))
    candidates = [m for m in candidates if m not in user_history]
    return candidates[:n_candidates]

def compute_features_for_candidates(user_id, candidate_movie_ids, ratings, movies, 
                                    user_stats, item_stats, user_genre_prefs):
    # Base dataframe
    candidates_df = pd.DataFrame({
        'UserID': [user_id] * len(candidate_movie_ids),
        'MovieID': candidate_movie_ids
    })
    
    # Merge stats
    candidates_df = candidates_df.merge(user_stats, on='UserID', how='left')
    candidates_df = candidates_df.merge(item_stats, on='MovieID', how='left')
    candidates_df = candidates_df.loc[:, ~candidates_df.columns.duplicated()]
    
    # User interaction features
    user_history = ratings[ratings['UserID'] == user_id]
    if not user_history.empty:
        candidates_df['user_rating_std'] = user_history['Rating'].std()
        candidates_df['user_rating_median'] = user_history['Rating'].median()
    else:
        candidates_df['user_rating_std'] = 0
        candidates_df['user_rating_median'] = 3.0
    
    candidates_df['rating_deviation_from_user_avg'] = (
        candidates_df['item_avg_rating'] - candidates_df['user_avg_rating']
    )
    
    # Genre features
    genre_cols = [c for c in movies.columns if c not in ["MovieID", "Title", "Release_Year"]]
    candidates_df = candidates_df.merge(movies[['MovieID'] + genre_cols], on='MovieID', how='left')
    candidates_df = candidates_df.merge(user_genre_prefs, on='UserID', how='left')
    candidates_df = candidates_df.loc[:, ~candidates_df.columns.duplicated()]
    
    user_pref_cols = [c for c in user_genre_prefs.columns if c.startswith("user_pref_")]
    genre_cols_actual = [c for c in genre_cols if c in candidates_df.columns]
    user_pref_cols_actual = [c for c in user_pref_cols if c in candidates_df.columns]
    
    for col in user_pref_cols_actual + genre_cols_actual:
        candidates_df[col] = candidates_df[col].fillna(0)
    
    # Compute cosine similarity
    if user_pref_cols_actual and genre_cols_actual:
        user_vectors = candidates_df[user_pref_cols_actual].values
        item_vectors = candidates_df[genre_cols_actual].values
        
        dot_product = np.sum(user_vectors * item_vectors, axis=1)
        user_norm = np.linalg.norm(user_vectors, axis=1)
        item_norm = np.linalg.norm(item_vectors, axis=1)
        
        candidates_df['genre_cosine_similarity'] = np.divide(
            dot_product, user_norm * item_norm,
            out=np.zeros_like(dot_product),
            where=(user_norm * item_norm) != 0
        )
        candidates_df['genre_overlap_count'] = ((user_vectors > 0) & (item_vectors > 0)).sum(axis=1)
        candidates_df = candidates_df.drop(columns=genre_cols_actual + user_pref_cols_actual, errors='ignore')
    else:
        candidates_df['genre_cosine_similarity'] = 0
        candidates_df['genre_overlap_count'] = 0
    
    # Temporal features
    current_year = 2003
    candidates_df['movie_age_years'] = current_year - candidates_df['Release_Year']
    candidates_df['movie_age_years'] = candidates_df['movie_age_years'].fillna(
        candidates_df['movie_age_years'].median()
    )
    candidates_df['is_recent_movie'] = (candidates_df['movie_age_years'] <= 5).astype(int)
    candidates_df['rating_recency'] = 0.5
    
    # Popularity features
    candidates_df['item_rating_count_log'] = np.log1p(candidates_df['item_rating_count'])
    candidates_df['user_rating_count_log'] = np.log1p(candidates_df['user_rating_count'])
    candidates_df['item_popularity_score'] = (
        candidates_df['item_rating_count'] * candidates_df['item_avg_rating']
    )
    candidates_df['item_popularity_score_log'] = np.log1p(candidates_df['item_popularity_score'])
    
    return candidates_df

def recommend_for_user(user_id, model, feature_cols, ratings, movies, 
                      user_stats, item_stats, user_genre_prefs, top_k=10):
    # Generate candidates
    candidates = generate_candidates_for_user(
        user_id, ratings, movies, item_stats, user_genre_prefs
    )
    
    if not candidates:
        return None
    
    # Compute features
    candidates_df = compute_features_for_candidates(
        user_id, candidates, ratings, movies, user_stats, item_stats, user_genre_prefs
    )
    
    # Ensure all features exist
    for f in feature_cols:
        if f not in candidates_df.columns:
            candidates_df[f] = 0
    
    # Score candidates
    X = candidates_df[feature_cols].values
    scores = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X)
    candidates_df['score'] = scores
    
    # FIXED: Merge with movies to get Title and Release_Year
    candidates_df = candidates_df.merge(
        movies[['MovieID', 'Title', 'Release_Year']], 
        on='MovieID', 
        how='left',
        suffixes=('', '_movie')
    )
    
    # Return top-K with all necessary fields
    recs = candidates_df.nlargest(top_k, 'score')
    
    return recs[[
        'MovieID', 'Title', 'Release_Year', 'score', 
        'item_avg_rating', 'item_rating_count'
    ]].reset_index(drop=True)

def main():
    print("="*70)
    print("INFERENCE VALIDATION")
    print("="*70)
    
    print("\nLoading model and data...")
    model, feature_cols = load_model("ranker_model.pkl")
    ratings, movies, user_stats, item_stats, user_genre_prefs = load_inference_data()
    
    print(f"Model loaded: {len(feature_cols)} features")
    
    print("\nGenerating recommendations for User 1...")
    recs = recommend_for_user(1, model, feature_cols, ratings, movies, 
                             user_stats, item_stats, user_genre_prefs, top_k=10)
    
    if recs is not None:
        print(f"\nTop-10 Recommendations:")
        print(recs[['Title', 'Release_Year', 'score', 'item_avg_rating']].to_string(index=False))
    
    print("\n"+"="*70)
    print("✓ Inference complete!")
    print("="*70)

if __name__ == "__main__":
    main()
