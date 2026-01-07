import pandas as pd
import numpy as np
import os

PROCESSED_DIR = "data/processed"
FEATURE_DIR = "data/features"

def load_data():
    ratings = pd.read_csv(os.path.join(PROCESSED_DIR, "ratings_processed.csv"))
    movies = pd.read_csv(os.path.join(PROCESSED_DIR, "movies_processed.csv"))
    user_stats = pd.read_csv(os.path.join(PROCESSED_DIR, "user_stats.csv"))
    item_stats = pd.read_csv(os.path.join(PROCESSED_DIR, "item_stats.csv"))
    user_genre_prefs = pd.read_csv(os.path.join(PROCESSED_DIR, "user_genre_preferences.csv"))
    return ratings, movies, user_stats, item_stats, user_genre_prefs

def build_training_data(ratings, user_stats, item_stats):
    df = ratings.copy()
    df = df.merge(user_stats, on="UserID", how="left")
    df = df.merge(item_stats, on="MovieID", how="left", suffixes=('', '_item'))
    df = df.loc[:, ~df.columns.duplicated()]
    return df

def add_interaction_features(df, ratings):
    user_history = ratings.groupby("UserID").agg(
        user_rating_std=("Rating", "std"),
        user_rating_median=("Rating", "median")
    ).reset_index()
    df = df.merge(user_history, on="UserID", how="left", suffixes=('', '_hist'))
    df = df.loc[:, ~df.columns.duplicated()]
    df["rating_deviation_from_user_avg"] = df["item_avg_rating"] - df["user_avg_rating"]
    df["user_rating_std"] = df["user_rating_std"].fillna(0)
    return df

def add_genre_features(df, user_genre_prefs, movies):
    genre_cols = [c for c in movies.columns if c not in ["MovieID", "Title", "Release_Year"]]
    user_pref_cols = [c for c in user_genre_prefs.columns if c.startswith("user_pref_")]
    
    if not any(c in df.columns for c in user_pref_cols):
        df = df.merge(user_genre_prefs, on="UserID", how="left", suffixes=('', '_pref'))
        df = df.loc[:, ~df.columns.duplicated()]
    
    genre_cols_actual = [c for c in genre_cols if c in df.columns]
    user_pref_cols_actual = [c for c in user_pref_cols if c in df.columns]
    
    for col in user_pref_cols_actual + genre_cols_actual:
        df[col] = df[col].fillna(0)
    
    user_vectors = df[user_pref_cols_actual].values
    item_vectors = df[genre_cols_actual].values
    
    dot_product = np.sum(user_vectors * item_vectors, axis=1)
    user_norm = np.linalg.norm(user_vectors, axis=1)
    item_norm = np.linalg.norm(item_vectors, axis=1)
    
    df["genre_cosine_similarity"] = np.divide(
        dot_product, user_norm * item_norm,
        out=np.zeros_like(dot_product),
        where=(user_norm * item_norm) != 0
    )
    df["genre_overlap_count"] = ((user_vectors > 0) & (item_vectors > 0)).sum(axis=1)
    df = df.drop(columns=genre_cols_actual + user_pref_cols_actual, errors='ignore')
    return df

def add_temporal_features(df):
    current_year = 2003
    df["movie_age_years"] = current_year - df["Release_Year"]
    df["movie_age_years"] = df["movie_age_years"].fillna(df["movie_age_years"].median())
    df["is_recent_movie"] = (df["movie_age_years"] <= 5).astype(int)
    df["rating_recency"] = (df["Timestamp"] - df["Timestamp"].min()) / (df["Timestamp"].max() - df["Timestamp"].min())
    return df

def add_popularity_features(df):
    df["item_rating_count_log"] = np.log1p(df["item_rating_count"])
    df["user_rating_count_log"] = np.log1p(df["user_rating_count"])
    df["item_popularity_score"] = df["item_rating_count"] * df["item_avg_rating"]
    df["item_popularity_score_log"] = np.log1p(df["item_popularity_score"])
    return df

def select_features(df):
    drop_cols = ["user_first_ts", "user_last_ts", "item_first_ts", "item_last_ts", "Release_Year"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors='ignore')
    
    id_cols = ["UserID", "MovieID"]
    label_cols = ["Rating", "Relevance"]
    metadata_cols = ["Title", "Timestamp"]
    feature_cols = [c for c in df.columns if c not in id_cols + label_cols + metadata_cols]
    
    col_order = id_cols + feature_cols + label_cols + metadata_cols
    col_order = [c for c in col_order if c in df.columns]
    return df[col_order], feature_cols

def main():
    print("="*70)
    print("FEATURE ENGINEERING")
    print("="*70)
    
    ratings, movies, user_stats, item_stats, user_genre_prefs = load_data()
    
    df = build_training_data(ratings, user_stats, item_stats)
    df = add_interaction_features(df, ratings)
    df = add_genre_features(df, user_genre_prefs, movies)
    df = add_temporal_features(df)
    df = add_popularity_features(df)
    df, feature_cols = select_features(df)
    
    os.makedirs(FEATURE_DIR, exist_ok=True)
    df.to_csv(os.path.join(FEATURE_DIR, "training_data.csv"), index=False)
    pd.DataFrame({"feature": feature_cols}).to_csv(
        os.path.join(FEATURE_DIR, "feature_names.csv"), index=False
    )
    
    print(f"\n✓ Training data saved: {df.shape}")
    print(f"  Features: {len(feature_cols)}")
    print(f"  Positive samples: {df['Relevance'].sum():,} ({df['Relevance'].mean():.2%})")
    print("="*70)

if __name__ == "__main__":
    main()