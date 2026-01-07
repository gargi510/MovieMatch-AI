import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRanker
import warnings
warnings.filterwarnings('ignore')

FEATURE_DIR = "data/features"
MODEL_DIR = "models"

def load_training_data():
    df = pd.read_csv(os.path.join(FEATURE_DIR, "training_data.csv"))
    feature_names = pd.read_csv(os.path.join(FEATURE_DIR, "feature_names.csv"))
    return df, feature_names["feature"].tolist()

def split_by_users(df, test_size=0.2, random_state=42):
    users = df["UserID"].unique()
    np.random.seed(random_state)
    test_users = np.random.choice(users, size=int(len(users) * test_size), replace=False)
    train_users = np.setdiff1d(users, test_users)
    
    train_df = df[df["UserID"].isin(train_users)].copy()
    test_df = df[df["UserID"].isin(test_users)].copy()
    return train_df, test_df

def prepare_model_data(df, feature_cols):
    return df[feature_cols].values, df["Relevance"].values, df["UserID"].values

def train_baseline(X_train, y_train, X_test, y_test):
    model = XGBClassifier(
        n_estimators=100, max_depth=6, learning_rate=0.1,
        objective='binary:logistic', random_state=42, eval_metric='logloss'
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    return model

def train_ranker(X_train, y_train, qid_train, X_test, y_test, qid_test):
    model = XGBRanker(
        n_estimators=100, max_depth=6, learning_rate=0.1,
        objective='rank:ndcg', random_state=42
    )
    model.fit(X_train, y_train, qid=qid_train, 
              eval_set=[(X_test, y_test)], eval_qid=[qid_test], verbose=False)
    return model

def dcg_at_k(y_true, y_scores, k=10):
    k = min(k, len(y_true))
    order = np.argsort(y_scores)[::-1][:k]
    gains = y_true[order]
    discounts = np.log2(np.arange(2, len(gains) + 2))
    return (gains / discounts).sum()

def ndcg_at_k(y_true, y_pred, k=10):
    dcg = dcg_at_k(y_true, y_pred, k)
    k = min(k, len(y_true))
    ideal_order = np.argsort(y_true)[::-1][:k]
    ideal_gains = y_true[ideal_order]
    ideal_discounts = np.log2(np.arange(2, len(ideal_gains) + 2))
    idcg = (ideal_gains / ideal_discounts).sum()
    return (dcg / idcg) if idcg > 0 else 0.0

def precision_at_k(y_true, y_pred, k=10):
    k = min(k, len(y_true))
    top_k_idx = np.argsort(y_pred)[::-1][:k]
    return y_true[top_k_idx].sum() / k if len(y_true) > 0 else 0

def recall_at_k(y_true, y_pred, k=10):
    n_relevant = y_true.sum()
    if n_relevant == 0:
        return 0
    k = min(k, len(y_true))
    top_k_idx = np.argsort(y_pred)[::-1][:k]
    return y_true[top_k_idx].sum() / n_relevant

def evaluate_model(model, X_test, y_test, qid_test, k=10):
    y_pred = model.predict_proba(X_test)[:, 1] if isinstance(model, XGBClassifier) else model.predict(X_test)
    
    test_df = pd.DataFrame({'UserID': qid_test, 'y_true': y_test, 'y_pred': y_pred})
    metrics = []
    
    for user_id, group in test_df.groupby('UserID'):
        y_true, y_pred = group['y_true'].values, group['y_pred'].values
        if y_true.sum() == 0 or len(y_true) < k:
            continue
        metrics.append({
            'precision': precision_at_k(y_true, y_pred, k),
            'recall': recall_at_k(y_true, y_pred, k),
            'ndcg': ndcg_at_k(y_true, y_pred, k)
        })
    
    metrics_df = pd.DataFrame(metrics)
    return {
        'precision@10': metrics_df['precision'].mean(),
        'recall@10': metrics_df['recall'].mean(),
        'ndcg@10': metrics_df['ndcg'].mean()
    }

def save_models(baseline, ranker, feature_cols):
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(os.path.join(MODEL_DIR, "baseline_model.pkl"), "wb") as f:
        pickle.dump(baseline, f)
    with open(os.path.join(MODEL_DIR, "ranker_model.pkl"), "wb") as f:
        pickle.dump(ranker, f)
    pd.DataFrame({"feature": feature_cols}).to_csv(
        os.path.join(MODEL_DIR, "feature_names.csv"), index=False
    )

def main():
    print("="*70)
    print("RANKING MODEL TRAINING")
    print("="*70)
    
    df, feature_cols = load_training_data()
    train_df, test_df = split_by_users(df)
    
    X_train, y_train, qid_train = prepare_model_data(train_df, feature_cols)
    X_test, y_test, qid_test = prepare_model_data(test_df, feature_cols)
    
    print("\nTraining baseline...")
    baseline = train_baseline(X_train, y_train, X_test, y_test)
    
    print("Training ranker...")
    ranker = train_ranker(X_train, y_train, qid_train, X_test, y_test, qid_test)
    
    print("\nEvaluating models...")
    baseline_results = evaluate_model(baseline, X_test, y_test, qid_test)
    ranker_results = evaluate_model(ranker, X_test, y_test, qid_test)
    
    print(f"\nBaseline - NDCG@10: {baseline_results['ndcg@10']:.4f}, "
          f"Precision@10: {baseline_results['precision@10']:.4f}")
    print(f"Ranker   - NDCG@10: {ranker_results['ndcg@10']:.4f}, "
          f"Precision@10: {ranker_results['precision@10']:.4f}")
    
    save_models(baseline, ranker, feature_cols)
    print("\n✓ Models saved!")
    print("="*70)

if __name__ == "__main__":
    main()
