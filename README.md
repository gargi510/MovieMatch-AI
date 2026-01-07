# 🎬 MovieMatch AI

**Production-Grade Movie Recommendation System using Learning-to-Rank**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-orange.svg)](https://xgboost.readthedocs.io/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![AWS ECS Deployment](https://img.shields.io/badge/deployed%20on-AWS%20ECS-232F3E.svg?style=flat-square)](https://aws.amazon.com/ecs/)

---

## 🎯 Overview

MovieMatch AI is a **two-stage Learning-to-Rank (LTR)** recommendation system that addresses critical limitations in traditional rating prediction approaches. Unlike conventional systems optimizing RMSE/MAE, this system directly optimizes **NDCG@10** — what users actually experience.

### Key Features

- 🏆 **87.6% NDCG@10** - Industry-leading ranking quality
- ⚡ **Sub-100ms latency** - Real-time recommendations
- 🆕 **100% cold-start coverage** - Handles new users via demographics + location
- 📍 **Location-aware** - Regional preference blending using zipcode
- 🎯 **Production-ready** - Complete REST API + Web UI 
- ☁️ **Deployed on AWS ECS** - Fully cloud-hosted for scalability and availability

---

## 📊 The Problem

Traditional recommendation systems face three critical challenges:

### 1. **Wrong Optimization Target**
- **Rating Prediction (RMSE)** ≠ **Good Rankings**
- Users only see top-10 items, not all predictions
- A model with perfect RMSE=0 could still rank poorly

### 2. **Cold-Start Problem**
- **100% of new users** have no interaction history
- Collaborative filtering fails completely
- Missing ~20-40% of potential users at any time

### 3. **Scale & Speed**
- Ranking 4K movies for 6K users = **24M computations**
- Real-time systems need **<100ms latency**
- Most items are irrelevant noise

---

## 🏗️ Solution Architecture

### Two-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: Candidate Generation (Recall)                     │
├─────────────────────────────────────────────────────────────┤
│  • Popularity-based (Top 100)                               │
│  • Genre similarity (Top 150)                               │
│  → Output: ~200 high-recall candidates/user                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: Learning-to-Rank (Precision)                      │
├─────────────────────────────────────────────────────────────┤
│  • XGBoost LambdaMART (rank:ndcg)                           │
│  • 20 engineered features                                   │
│  → Output: Top-10 ranked recommendations                    │
└─────────────────────────────────────────────────────────────┘
```

### Cold-Start Strategy

```
New User → Demographic Match (Age/Gender/Occupation)
              ↓
        Regional Match (Zipcode → NE/S/MW/W)
              ↓
        Blend: 60% Demographics + 40% Regional
              ↓
        Fallback: Global Popular Movies
```

---

## 📈 Results

MovieMatch AI achieves **87.6% NDCG@10**, **sub-100ms latency**, and strong precision/recall metrics for top-10 recommendations.  

See [RESULTS.md](RESULTS.md) for the full evaluation and feature analysis.

---

## 🚀 Quick Start

For detailed setup, dataset instructions, and running the pipeline & application, see [QUICKSTART.md](QUICKSTART.md).

Quick clone and install dependencies:

```bash
git clone https://github.com/yourusername/moviematch-ai.git
cd moviematch-ai
pip install -r requirements.txt 
```
---

## 🗂️ Project Structure
```
MOVIE LATCH AI/
├── data/
│   ├── raw/                   # MovieLens 1M data
│   ├── processed/             # Cleaned data + statistics
│   ├── candidates/            # Stage 1 (Retrieval) output
│   └── features/              # Stage 2 (Ranking) input
├── logs/                      # Pipeline logs
├── models/                    # Trained XGBoost models
├── src/
│   ├── EDA.ipynb              # EDA on user, movie, ratings dataset (not part of pipeline) 
│   ├── data_loader.py         # Load user, movie, ratings dataset 
│   ├── preprocessing.py       # Data cleaning + feature aggregation
│   ├── candidate_generation.py # Generating candidate pool
│   ├── feature_engineering.py  # Feature creation
│   ├── ranking_model.py       # XGBoost LambdaMART training
│   ├── cold_start_handler.py   # New user recommendations
│   └── inference.py           # Prediction pipeline
├── app.py                     # Flask REST API
├── streamlit_demo.py          # Web UI
├── run_pipeline.py            # End-to-end orchestrator
├── requirements.txt           # Project dependencies
├── Dockerfile                 # Containerization config
├── quickstart.md              # Rapid setup guide
├── results.md                 # Model performance metrics
└── README.md                  # Project overview and documentation
```

---

## 🔬 Methodology

### Exploratory Data Analysis

The full exploratory data analysis of the MovieLens dataset has been done in [`EDA.ipynb`](src/EDA.ipynb).  
This notebook is **separate from the main pipeline** and demonstrates dataset insights, distributions, and initial visualizations.


### 1. Feature Engineering (20 Features)

| Category | Features | Examples |
|----------|----------|----------|
| **User** | 8 features | avg_rating, rating_count, genre_preferences |
| **Item** | 6 features | popularity, avg_rating, tenure |
| **Interaction** | 4 features | genre_similarity, rating_deviation |
| **Temporal** | 2 features | movie_age, rating_recency |

### 2. Learning-to-Rank

**Why LambdaMART?**
- ✅ Directly optimizes **NDCG** (not RMSE)
- ✅ Pairwise loss learns relative rankings
- ✅ Handles position bias naturally

**Training Strategy:**
- Train on **all 1M historical ratings** (not just candidates)
- Split by **users** (not ratings) to prevent leakage
- Group by user (query groups) for ranking loss

### 3. Evaluation

**Primary Metric: NDCG@10**
- Position-aware: #1 slot matters more than #10
- Aligned with user experience
- Industry standard for ranking systems

---

## 📚 Tech Stack

**Core:**  
- Python 3.9+  
- XGBoost 2.0+ (LambdaMART)  
- Pandas, NumPy  

**Deployment:**  
- Flask (REST API)  
- Streamlit (Web UI)  
- Docker (Containerization)  
- AWS ECS (Cloud Deployment)  

**Data:**  
- MovieLens 1M (1M ratings, 6K users, 4K movies)


---

## 🐳 Docker & AWS Deployment

MovieMatch AI can be run locally using Docker or deployed on **AWS ECS** for scalable, cloud-hosted recommendations.

### Local Docker

```bash
# Build Docker image
docker build -t moviematch-ai .

# Run container (API + Streamlit UI)
docker run -p 5000:5000 -p 8501:8501 moviematch-ai
```

Access using: http://localhost:8501/
---

## 📖 API Documentation

### Existing User Recommendations
```http
POST /recommend
Content-Type: application/json

{
  "user_id": 1,
  "top_k": 10
}
```

### New User Recommendations
```http
POST /recommend/new-user
Content-Type: application/json

{
  "demographics": {
    "gender": "F",
    "age": 25,
    "occupation": 4,
    "zipcode": "90210"  // Optional
  },
  "top_k": 10
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "title": "Shawshank Redemption, The",
      "release_year": 1994,
      "genres": "Crime|Drama",
      "avg_rating": 4.55,
      "num_ratings": 2227
    }
  ],
  "latency_ms": 78.3
}
```

---

## 🎓 Key Design Decisions

### Two-Stage Pipeline
✅ High recall → High precision (~200 candidates)  
✅ 100x faster inference  
❌ Avoids ranking all 4K movies (24M computations, mostly irrelevant)  

### Train on All Ratings
✅ Clear labels (rating ≥ 4)  
✅ Unbiased historical interactions  
✅ Better generalization  

### LambdaMART
✅ Directly optimizes **NDCG**  
✅ Position-aware top-k ranking  
✅ Interpretable features  
❌ Avoids RMSE-only methods like SVD/ALS


---

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **MovieLens 1M Dataset** - GroupLens Research
- **XGBoost** - Chen & Guestrin (2016)
- **Learning-to-Rank** - Burges et al. (2010)

---

## 📧 Contact

**Author:** Gargi Mishra  
**Email:** [gargi.mishra51095@gmail.com](mailto:gargi.mishra51095@gmail.com)  
**LinkedIn:** [linkedin.com/in/gargi510](https://www.linkedin.com/in/gargi510/)

---

**⭐ If you find this project helpful, please give it a star on GitHub!**
