import os
import sys
import time
import importlib.util
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def verify_files(file_list):
    missing = [f for f in file_list if not os.path.exists(f)]
    if missing:
        for f in missing:
            print(f"  ❌ Missing: {f}")
        return False
    print(f"  ✓ {len(file_list)} files verified")
    return True

def stage_0_data_check():
    print("\n[STAGE 0] Validating Raw Data...")
    return verify_files([
        "data/raw/users.dat",
        "data/raw/movies.dat",
        "data/raw/ratings.dat"
    ])

def stage_1_preprocessing():
    print("\n[STAGE 1] Preprocessing...")
    try:
        load_module("preprocessing", "src/preprocessing.py").main()
        return verify_files([
            "data/processed/ratings_processed.csv",
            "data/processed/user_stats.csv"
        ])
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def stage_2_candidates():
    print("\n[STAGE 2] Candidate Generation...")
    try:
        load_module("candidate_gen", "src/candidate_generation.py").main()
        return verify_files(["data/candidates/user_movie_candidates.csv"])
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def stage_3_features():
    print("\n[STAGE 3] Feature Engineering...")
    try:
        load_module("feat_eng", "src/feature_engineering.py").main()
        return verify_files(["data/features/training_data.csv"])
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def stage_4_training():
    print("\n[STAGE 4] Model Training...")
    try:
        load_module("ranking", "src/ranking_model.py").main()
        
        print("\n  Building cold-start profiles...")
        load_module("cold_start", "src/cold_start_handler.py").ColdStartHandler()
        
        return verify_files([
            "models/ranker_model.pkl",
            "models/feature_names.csv"
        ])
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def stage_5_inference():
    print("\n[STAGE 5] Validation...")
    try:
        # Load inference module
        inf = load_module("inference", "src/inference.py")
        
        print("  Testing existing user recommendations...")
        model, feature_cols = inf.load_model("ranker_model.pkl")
        ratings, movies, user_stats, item_stats, user_genre_prefs = inf.load_inference_data()
        
        recs = inf.recommend_for_user(
            1, model, feature_cols, ratings, movies,
            user_stats, item_stats, user_genre_prefs, top_k=3
        )
        
        if recs is not None:
            print(f"    ✓ User 1: {len(recs)} recommendations generated")
        
        # Test cold-start
        print("  Testing new user recommendations...")
        cs = load_module("cold_start", "src/cold_start_handler.py")
        handler = cs.ColdStartHandler()
        
        recs_cold = handler.recommend(
            user_demographics={'gender': 'F', 'age': 25, 'occupation': 4},
            top_k=3
        )
        
        if recs_cold is not None:
            print(f"    ✓ New user: {len(recs_cold)} recommendations generated")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*70)
    print("MOVIEMATCH AI - TRAINING PIPELINE")
    print("="*70)
    
    start_time = time.time()
    
    stages = [
        stage_0_data_check,
        stage_1_preprocessing,
        stage_2_candidates,
        stage_3_features,
        stage_4_training,
        stage_5_inference
    ]
    
    for i, stage_fn in enumerate(stages, 1):
        stage_start = time.time()
        if not stage_fn():
            print(f"\n❌ Pipeline failed at stage {i}: {stage_fn.__name__}")
            sys.exit(1)
        stage_duration = time.time() - stage_start
        print(f"  ⏱️  Stage completed in {stage_duration:.1f}s")
    
    total_duration = time.time() - start_time
    
    print("\n"+"="*70)
    print(f"✅ SUCCESS: Pipeline completed in {total_duration:.1f}s")
    print("\nNext steps:")
    print("  1. Start API: python app.py")
    print("  2. Start UI:  streamlit run streamlit_app.py")
    print("="*70)

if __name__ == "__main__":
    main()