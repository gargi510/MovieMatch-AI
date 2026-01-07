import pandas as pd
import numpy as np
import os

PROCESSED_DIR = "data/processed"

def extract_region_from_zipcode(zipcode):
    if pd.isna(zipcode) or zipcode == '':
        return 'Other'
    zipcode = str(zipcode).strip()
    if len(zipcode) < 1:
        return 'Other'
    region_map = {
        '0': 'Northeast', '1': 'Northeast',
        '2': 'South', '3': 'South', '6': 'South', '7': 'South',
        '4': 'Midwest', '5': 'Midwest',
        '8': 'West', '9': 'West'
    }
    return region_map.get(zipcode[0], 'Other')

class ColdStartHandler:
    def __init__(self):
        self.load_data()
        self.build_demographic_profiles()
        self.build_regional_profiles()
    
    def load_data(self):
        self.ratings = pd.read_csv(os.path.join(PROCESSED_DIR, "ratings_processed.csv"))
        self.movies = pd.read_csv(os.path.join(PROCESSED_DIR, "movies_processed.csv"))
        self.users = pd.read_csv(os.path.join(PROCESSED_DIR, "users_processed.csv"))
        self.item_stats = pd.read_csv(os.path.join(PROCESSED_DIR, "item_stats.csv"))
    
    def build_demographic_profiles(self):
        ratings_with_demo = self.ratings.merge(
            self.users[['UserID', 'Gender', 'Age', 'Occupation']],
            on='UserID', how='left'
        )
        demographic_groups = ratings_with_demo[
            ratings_with_demo['Rating'] >= 4
        ].groupby(['Gender', 'Age', 'Occupation'])
        profiles = []
        for (gender, age, occupation), group in demographic_groups:
            top_movies = group.groupby('MovieID').agg(
                avg_rating=('Rating', 'mean'),
                rating_count=('Rating', 'count')
            ).reset_index()
            top_movies = top_movies[top_movies['rating_count'] >= 5]
            top_movies['score'] = top_movies['avg_rating'] * np.log1p(top_movies['rating_count'])
            top_movies = top_movies.nlargest(50, 'score')
            profiles.append({
                'gender': gender,
                'age': age,
                'occupation': occupation,
                'top_movies': top_movies['MovieID'].tolist()
            })
        self.demographic_profiles = pd.DataFrame(profiles)
    
    def build_regional_profiles(self):
        self.users['region'] = self.users['ZipCode'].apply(extract_region_from_zipcode)
        ratings_with_region = self.ratings.merge(
            self.users[['UserID', 'region']], on='UserID', how='left'
        )
        regional_groups = ratings_with_region[
            ratings_with_region['Rating'] >= 4
        ].groupby('region')
        profiles = []
        for region, group in regional_groups:
            top_movies = group.groupby('MovieID').agg(
                avg_rating=('Rating', 'mean'),
                rating_count=('Rating', 'count')
            ).reset_index()
            top_movies = top_movies[top_movies['rating_count'] >= 10]
            top_movies['score'] = top_movies['avg_rating'] * np.log1p(top_movies['rating_count'])
            top_movies = top_movies.nlargest(100, 'score')
            profiles.append({
                'region': region,
                'n_users': group['UserID'].nunique(),
                'top_movies': top_movies['MovieID'].tolist()
            })
        self.regional_profiles = pd.DataFrame(profiles)
    
    def get_cold_start_user_recommendations(self, user_demographics, top_k=10):
        gender = user_demographics.get('gender', 'M')
        age = user_demographics.get('age', 25)
        occupation = user_demographics.get('occupation', 0)
        zipcode = user_demographics.get('zipcode', None)
        matching_profile = self.demographic_profiles[
            (self.demographic_profiles['gender'] == gender) &
            (self.demographic_profiles['age'] == age) &
            (self.demographic_profiles['occupation'] == occupation)
        ]
        demographic_movies = []
        if not matching_profile.empty:
            demographic_movies = matching_profile.iloc[0]['top_movies']
        else:
            matching_profile = self.demographic_profiles[
                (self.demographic_profiles['gender'] == gender) &
                (self.demographic_profiles['age'] == age)
            ]
            if not matching_profile.empty:
                all_movies = []
                for _, row in matching_profile.iterrows():
                    all_movies.extend(row['top_movies'])
                from collections import Counter
                demographic_movies = [m for m, _ in Counter(all_movies).most_common(100)]
        regional_movies = []
        if zipcode:
            region = extract_region_from_zipcode(zipcode)
            matching_region = self.regional_profiles[
                self.regional_profiles['region'] == region
            ]
            if not matching_region.empty:
                regional_movies = matching_region.iloc[0]['top_movies']
        if regional_movies:
            demo_count = int(top_k * 0.6)
            regional_count = top_k - demo_count
            combined_movies = demographic_movies[:demo_count] + regional_movies[:regional_count]
            seen = set()
            movies = []
            for m in combined_movies:
                if m not in seen:
                    seen.add(m)
                    movies.append(m)
            if len(movies) < top_k:
                for m in demographic_movies:
                    if m not in seen and len(movies) < top_k:
                        seen.add(m)
                        movies.append(m)
        else:
            movies = demographic_movies[:top_k]
        if not movies:
            movies = self.get_popular_movies(top_k)
        return movies[:top_k]
    
    def get_popular_movies(self, top_k=10):
        return (
            self.item_stats.sort_values('item_rating_count', ascending=False)
            .head(top_k)['MovieID'].tolist()
        )
    
    def recommend(self, user_id=None, user_demographics=None, top_k=10):
        if user_demographics is None:
            movie_ids = self.get_popular_movies(top_k)
        else:
            movie_ids = self.get_cold_start_user_recommendations(user_demographics, top_k)
        recommendations = self.movies[
            self.movies['MovieID'].isin(movie_ids)
        ].copy()
        genre_cols = [c for c in self.movies.columns if c not in ['MovieID', 'Title', 'Release_Year']]
        def get_genres(row):
            active = [g for g in genre_cols if row[g] == 1]
            return "|".join(active) if active else "Movie"
        recommendations['Genres'] = recommendations.apply(get_genres, axis=1)
        recommendations = recommendations.merge(
            self.item_stats[['MovieID', 'item_avg_rating', 'item_rating_count']],
            on='MovieID', how='left'
        )
        recommendations['order'] = recommendations['MovieID'].map(
            {mid: i for i, mid in enumerate(movie_ids)}
        )
        recommendations = recommendations.sort_values('order').drop('order', axis=1)
        return recommendations.head(top_k)

def main():
    handler = ColdStartHandler()
    new_user_demo = {'gender': 'F', 'age': 25, 'occupation': 4, 'zipcode': '90210'}
    recs = handler.recommend(user_demographics=new_user_demo, top_k=10)
    print(recs[['Title', 'Genres', 'item_avg_rating']].to_string(index=False))

if __name__ == "__main__":
    main()
