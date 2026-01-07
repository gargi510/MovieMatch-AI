# src/data_loader.py

import pandas as pd
import os

RAW_DIR = "data/raw"

# ----------------------------
# Data Loading Functions
# ----------------------------
def load_ratings(file_name="ratings.dat"):
    """Load raw ratings dataset as-is"""
    path = os.path.join(RAW_DIR, file_name)
    df = pd.read_csv(
        path,
        sep="::",
        engine='python',
        header=None,
        encoding='latin-1'
    )
    return df

def load_users(file_name="users.dat"):
    """Load raw users dataset as-is"""
    path = os.path.join(RAW_DIR, file_name)
    df = pd.read_csv(
        path,
        sep="::",
        engine='python',
        header=None,
        encoding='latin-1'
    )
    return df

def load_movies(file_name="movies.dat"):
    """Load raw movies dataset as-is"""
    path = os.path.join(RAW_DIR, file_name)
    df = pd.read_csv(
        path,
        sep="::",
        engine='python',
        header=None,
        encoding='latin-1'
    )
    return df

# ----------------------------
# Main loader
# ----------------------------
def main():
    ratings = load_ratings()
    users = load_users()
    movies = load_movies()
    
    print("Raw data loaded successfully!")
    print(f"Ratings shape: {ratings.shape}")
    print(f"Users shape: {users.shape}")
    print(f"Movies shape: {movies.shape}")

if __name__ == "__main__":
    main()
