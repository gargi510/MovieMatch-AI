# 🚀 Quick Start Guide

Get MovieMatch AI running in **5 minutes**.

---

## Prerequisites

### System Requirements
- **OS:** Linux, macOS, or Windows with WSL
- **RAM:** 8GB minimum
- **Disk:** 5GB free space
- **Python:** 3.9 or higher

### Check Python Version
```bash
python --version  # Should be 3.9+
```

---

## Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/moviematch-ai.git
cd moviematch-ai
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt:**
```
pandas==2.1.0
numpy==1.24.3
scikit-learn==1.3.0
xgboost==2.0.0
flask==2.3.3
flask-cors==4.0.0
streamlit==1.28.0
```

### Step 4: Download Dataset

**Option A: Manual Download**
1. Visit [MovieLens 1M](https://grouplens.org/datasets/movielens/1m/)
2. Download `ml-1m.zip`
3. Extract to `data/raw/`:
   ```
   data/raw/
   ├── users.dat
   ├── movies.dat
   └── ratings.dat
   ```

**Option B: Script (Linux/Mac)**
```bash
mkdir -p data/raw
cd data/raw
wget https://files.grouplens.org/datasets/movielens/ml-1m.zip
unzip ml-1m.zip
mv ml-1m/* .
rm -rf ml-1m ml-1m.zip
cd ../..
```

---

## Training the Model

### Run Complete Pipeline

```bash
python run_pipeline.py
```

**What happens:**
```
[STAGE 0] Validating raw data...          (5s)
[STAGE 1] Preprocessing...                 (15s)
[STAGE 2] Candidate generation...          (30s)
[STAGE 3] Feature engineering...           (25s)
[STAGE 4] Model training...                (20s)
[STAGE 5] Validation...                    (10s)

✓ Total: ~2 minutes
```

**Expected Output:**
```
============================================================
SUCCESS: Pipeline completed in 103.9s
Models and Cold-Start Profiles are ready for production
============================================================
```

### Verify Output

```bash
# Check trained models
ls models/
# Should see: ranker_model.pkl, baseline_model.pkl, feature_names.csv

# Check processed data
ls data/processed/
# Should see: ratings_processed.csv, movies_processed.csv, etc.
```

---

## Running the Application

### Option 1: Quick Demo (Streamlit Only)

```bash
streamlit run streamlit_app.py
```

**Access:** Open browser to `http://localhost:8501`

**Note:** This mode generates recommendations on-the-fly without the API server.

---

### Option 2: Full Deployment (API + UI)

**Terminal 1 - Start API Server:**
```bash
python app.py
```

**Output:**
```
======================================================================
INITIALIZING RECOMMENDATION SERVICE
======================================================================
✓ ALL RESOURCES LOADED - API READY
======================================================================

 * Running on http://0.0.0.0:5000
```

**Terminal 2 - Start Web Interface:**
```bash
streamlit run streamlit_app.py
```

**Output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501
```

**Access:**
- **Web UI:** `http://localhost:8501`
- **API:** `http://localhost:5000`

---

## Testing the System

### Test 1: Existing User (via Web UI)

1. Select **"Existing User"** mode
2. Enter User ID: `1`
3. Click **"🚀 Generate Recommendations"**

**Expected:** See 12 personalized movie recommendations in ~80ms

---

### Test 2: New User without Zipcode

1. Select **"New User"** mode
2. Enter:
   - Gender: `F`
   - Age: `25`
   - Occupation: `4` (Student)
3. Click **"🎬 Discover Movies"**

**Expected:** Demographic-based recommendations

---

### Test 3: New User with Zipcode

1. Select **"New User"** mode
2. Enter:
   - Gender: `M`
   - Age: `35`
   - Occupation: `7`
   - Zipcode: `90210` (California - West region)
3. Click **"🎬 Discover Movies"**

**Expected:**
- Badge showing "📍 West Region Detected"
- Recommendations blending demographics (60%) + regional preferences (40%)

---

### Test 4: API Testing (curl)

**Existing User:**
```bash
curl -X POST http://localhost:5000/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "top_k": 10}'
```

**New User (with zipcode):**
```bash
curl -X POST http://localhost:5000/recommend/new-user \
  -H "Content-Type: application/json" \
  -d '{
    "demographics": {
      "gender": "F",
      "age": 25,
      "occupation": 4,
      "zipcode": "10001"
    },
    "top_k": 10
  }'
```

---

## Understanding the UI

### Sidebar Controls

| Setting | Purpose | Default |
|---------|---------|---------|
| **API URL** | Backend endpoint | `http://localhost:5000` |
| **Number of Results** | Recommendations to show | `12` |
| **Selection Mode** | User type | `Existing User` |

### Existing User Mode

**Inputs:**
- User ID (1-6040)

**Output:**
- Top-K personalized recommendations
- Latency badge (ms)
- Movie cards with ratings

### New User Mode

**Inputs:**
- Gender (M/F)
- Age Group (1, 18, 25, 35, 45, 50, 56)
- Occupation ID (0-20)
- Zipcode (optional, 5 digits)

**Output:**
- Demographic + location-aware recommendations
- Region badge (if zipcode provided)
- Info box explaining strategy

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'xgboost'`

**Solution:**
```bash
pip install xgboost==2.0.0
```

---

### Issue: `FileNotFoundError: data/raw/users.dat`

**Solution:**
Download dataset (see Step 4 above) and verify:
```bash
ls data/raw/
# Should show: users.dat, movies.dat, ratings.dat
```

---

### Issue: API Connection Error in Streamlit

**Solution:**
1. Verify API is running: `curl http://localhost:5000`
2. Check firewall settings
3. Use correct API URL in sidebar

---

### Issue: Port Already in Use

**Flask (5000):**
```bash
# Kill process using port
lsof -ti:5000 | xargs kill -9

# Or use different port
python app.py --port 5001
```

**Streamlit (8501):**
```bash
streamlit run streamlit_app.py --server.port 8502
```

---

## Next Steps

### Explore the System
- ✅ Try different user IDs (1-6040)
- ✅ Test various demographic combinations
- ✅ Compare zipcode regions (90210, 10001, 60601)
- ✅ Adjust top_k slider

### Read Documentation
- 📖 [README.md](README.md) - Full project overview
- 📊 [RESULTS.md](RESULTS.md) - Detailed metrics and analysis

### Customize the System
- 🎨 Modify `streamlit_app.py` for UI changes
- 🔧 Tune hyperparameters in `src/ranking_model.py`
- 📈 Add features in `src/feature_engineering.py`

---

## Docker Deployment (Advanced)

```bash
# Build image
docker build -t moviematch-ai .

# Run container
docker run -d -p 5000:5000 -p 8501:8501 moviematch-ai

# Check logs
docker logs -f <container_id>
```

**Access:** Same as local deployment (ports 5000, 8501)

---

**Happy recommending! 🎬**