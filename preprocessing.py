import pandas as pd
import os

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

def save_processed(df, file_name):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    df.to_csv(os.path.join(PROCESSED_DIR, file_name), index=False)

def preprocess_users(file_name="users.dat"):
    df = pd.read_csv(
        os.path.join(RAW_DIR, file_name),
        sep="::", engine="python", header=None, encoding="latin-1"
    )
    df.columns = ["UserID", "Gender", "Age", "Occupation", "ZipCode"]
    df["UserID"] = pd.to_numeric(df["UserID"], errors="coerce")
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    df["Occupation"] = df["Occupation"].astype("category")
    save_processed(df, "users_processed.csv")
    return df

def preprocess_movies(file_name="movies.dat"):
    df = pd.read_csv(
        os.path.join(RAW_DIR, file_name),
        sep="::", engine="python", header=None, encoding="latin-1"
    )
    df.columns = ["MovieID", "Title", "Genres"]
    df["MovieID"] = pd.to_numeric(df["MovieID"], errors="coerce")
    df["Release_Year"] = pd.to_numeric(df["Title"].str.extract(r"\((\d{4})\)")[0], errors="coerce")
    df["Title"] = df["Title"].str.replace(r"\(\d{4}\)", "", regex=True).str.strip()
    
    genre_dummies = df["Genres"].str.get_dummies(sep="|")
    df = pd.concat([df.drop(columns=["Genres"]), genre_dummies], axis=1)
    save_processed(df, "movies_processed.csv")
    return df

def preprocess_ratings(file_name="ratings.dat"):
    df = pd.read_csv(
        os.path.join(RAW_DIR, file_name),
        sep="::", engine="python", header=None, encoding="latin-1"
    )
    df.columns = ["UserID", "MovieID", "Rating", "Timestamp"]
    df = df.apply(pd.to_numeric, errors="coerce")
    df["Relevance"] = (df["Rating"] >= 4).astype(int)
    save_processed(df, "ratings_processed.csv")
    return df

def compute_basic_features():
    ratings = pd.read_csv(os.path.join(PROCESSED_DIR, "ratings_processed.csv"))
    movies = pd.read_csv(os.path.join(PROCESSED_DIR, "movies_processed.csv"))
    
    # User stats
    user_stats = ratings.groupby("UserID").agg(
        user_avg_rating=("Rating", "mean"),
        user_rating_count=("Rating", "count"),
        user_positive_rate=("Relevance", "mean"),
        user_first_ts=("Timestamp", "min"),
        user_last_ts=("Timestamp", "max")
    ).reset_index()
    user_stats["user_tenure_days"] = (user_stats["user_last_ts"] - user_stats["user_first_ts"]) / 86400
    save_processed(user_stats, "user_stats.csv")
    
    # Item stats
    item_stats = ratings.groupby("MovieID").agg(
        item_avg_rating=("Rating", "mean"),
        item_rating_count=("Rating", "count"),
        item_positive_rate=("Relevance", "mean"),
        item_first_ts=("Timestamp", "min"),
        item_last_ts=("Timestamp", "max")
    ).reset_index()
    item_stats["item_tenure_days"] = (item_stats["item_last_ts"] - item_stats["item_first_ts"]) / 86400
    item_stats = item_stats.merge(movies, on="MovieID", how="left")
    save_processed(item_stats, "item_stats.csv")
    
    # User genre preferences
    genre_cols = [c for c in movies.columns if c not in ["MovieID", "Title", "Release_Year"]]
    ratings_with_genres = ratings.merge(movies[["MovieID"] + genre_cols], on="MovieID", how="left")
    
    user_genre_prefs = []
    for user_id, group in ratings_with_genres.groupby("UserID"):
        weighted_genres = (group[genre_cols].T * group["Rating"]).T.sum() / group["Rating"].sum()
        genre_dict = {"UserID": user_id}
        for genre in genre_cols:
            genre_dict[f"user_pref_{genre}"] = weighted_genres[genre]
        user_genre_prefs.append(genre_dict)
    
    save_processed(pd.DataFrame(user_genre_prefs), "user_genre_preferences.csv")

def main():
    print("="*60)
    print("PREPROCESSING PIPELINE")
    print("="*60)
    
    print("\n[1/4] Preprocessing users...")
    preprocess_users()
    
    print("[2/4] Preprocessing movies...")
    preprocess_movies()
    
    print("[3/4] Preprocessing ratings...")
    preprocess_ratings()
    
    print("[4/4] Computing aggregate features...")
    compute_basic_features()
    
    print("\n"+"="*60)
    print("✓ Preprocessing complete!")
    print("="*60)

if __name__ == "__main__":
    main()