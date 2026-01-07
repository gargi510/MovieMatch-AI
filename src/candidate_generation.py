import pandas as pd
import os

PROCESSED_DIR = "data/processed"
CANDIDATE_DIR = "data/candidates"
N_POPULAR = 100
N_GENRE = 150

def load_data():
    ratings = pd.read_csv(os.path.join(PROCESSED_DIR, "ratings_processed.csv"))
    movies = pd.read_csv(os.path.join(PROCESSED_DIR, "movies_processed.csv"))
    users = pd.read_csv(os.path.join(PROCESSED_DIR, "users_processed.csv"))
    return ratings, movies, users

def get_popular_movies(ratings):
    pop = (
        ratings.groupby("MovieID")
        .agg(rating_count=("Rating", "count"), avg_rating=("Rating", "mean"))
        .reset_index()
    )
    pop["popularity_score"] = pop["rating_count"] * pop["avg_rating"]
    return pop.sort_values("popularity_score", ascending=False).head(N_POPULAR)["MovieID"].tolist()

def get_genre_columns(movies):
    base_cols = {"MovieID", "Title", "Release_Year"}
    return [c for c in movies.columns if c not in base_cols]

def build_genre_candidates(ratings, movies):
    genre_cols = get_genre_columns(movies)
    ratings_genre = ratings.merge(movies[["MovieID"] + genre_cols], on="MovieID", how="left")
    
    candidates = []
    for user_id, group in ratings_genre.groupby("UserID"):
        liked = group[group["Rating"] >= 4]
        if liked.empty:
            continue
        
        genre_profile = liked[genre_cols].mean()
        movies["genre_score"] = movies[genre_cols].dot(genre_profile)
        user_seen = set(group["MovieID"])
        
        top_movies = (
            movies[~movies["MovieID"].isin(user_seen)]
            .sort_values("genre_score", ascending=False)
            .head(N_GENRE)["MovieID"]
            .tolist()
        )
        
        for mid in top_movies:
            candidates.append((user_id, mid, "genre_similarity"))
    
    return pd.DataFrame(candidates, columns=["UserID", "MovieID", "candidate_source"])

def main():
    os.makedirs(CANDIDATE_DIR, exist_ok=True)
    
    print("Loading data...")
    ratings, movies, users = load_data()
    
    print("Generating popularity candidates...")
    popular_movies = get_popular_movies(ratings)
    pop_candidates = pd.DataFrame(
        [(u, m, "popularity") for u in users["UserID"] for m in popular_movies],
        columns=["UserID", "MovieID", "candidate_source"]
    )
    
    print("Generating genre-based candidates...")
    genre_candidates = build_genre_candidates(ratings, movies)
    
    print("Combining candidates...")
    candidates = pd.concat([pop_candidates, genre_candidates])
    candidates = candidates.drop_duplicates(subset=["UserID", "MovieID"]).reset_index(drop=True)
    
    candidates.to_csv(os.path.join(CANDIDATE_DIR, "user_movie_candidates.csv"), index=False)
    print(f"Candidate generation completed!")
    print(f"Total candidates: {len(candidates):,}")

if __name__ == "__main__":
    main()
