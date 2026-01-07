import streamlit as st
import requests

st.set_page_config(page_title="MovieMatch AI", page_icon="🎬", layout="wide")

# Enhanced Modern Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp { 
        background: linear-gradient(135deg, #1a0933 0%, #2d1b4e 25%, #1f0a3c 50%, #0f051d 100%);
    }
    
    /* Main title styling */
    h1 {
        background: linear-gradient(135deg, #00f5ff 0%, #ff00ff 50%, #ffaa00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        font-size: 3.5rem !important;
        letter-spacing: -1px;
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a0933 0%, #2d1b4e 100%);
        border-right: 1px solid rgba(0, 245, 255, 0.2);
    }
    
    [data-testid="stSidebar"] h2 {
        color: #00f5ff;
        font-weight: 700;
        font-size: 1.3rem;
    }
    
    /* FIXED: Input field styling with BLACK text */
    .stTextInput input, .stNumberInput input {
        background: rgba(255, 255, 255, 0.95) !important;
        border: 1px solid rgba(0, 245, 255, 0.3) !important;
        color: #000000 !important;
        border-radius: 10px !important;
        font-weight: 600;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus {
        border: 1px solid #00f5ff !important;
        box-shadow: 0 0 0 1px rgba(0, 245, 255, 0.3) !important;
    }
    
    .stTextInput input::placeholder {
        color: #666666 !important;
        opacity: 0.7;
    }
    
    /* Slider styling */
    .stSlider [data-testid="stTickBar"] {
        background: rgba(0, 245, 255, 0.2);
    }
    
    /* Selectbox styling */
    .stSelectbox [data-baseweb="select"] {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        color: #000000 !important;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #00f5ff 0%, #ff00ff 100%);
        color: white;
        font-weight: 700;
        font-size: 16px;
        padding: 12px 40px;
        border-radius: 12px;
        border: none;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(0, 245, 255, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(0, 245, 255, 0.5);
    }
    
    /* Movie card styling */
    .movie-card {
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.08) 0%, rgba(255, 0, 255, 0.08) 100%);
        backdrop-filter: blur(20px);
        border-radius: 18px;
        padding: 24px;
        border: 1px solid rgba(0, 245, 255, 0.2);
        height: 300px;
        margin-bottom: 25px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .movie-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .movie-card:hover::before {
        left: 100%;
    }
    
    .movie-card:hover { 
        transform: translateY(-10px) scale(1.02);
        border: 1px solid #00f5ff;
        box-shadow: 0 20px 50px rgba(0, 245, 255, 0.3);
    }
    
    .movie-title { 
        font-size: 22px;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #00f5ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 6px;
        line-height: 1.3;
    }
    
    .movie-year { 
        font-size: 15px;
        color: #ffaa00;
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .genre-tag {
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.2) 0%, rgba(255, 0, 255, 0.2) 100%);
        color: #00f5ff;
        font-size: 11px;
        padding: 5px 12px;
        border-radius: 20px;
        border: 1px solid rgba(0, 245, 255, 0.4);
        margin-right: 6px;
        margin-bottom: 6px;
        display: inline-block;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    
    .genre-tag:hover {
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.3) 0%, rgba(255, 0, 255, 0.3) 100%);
        transform: scale(1.05);
    }
    
    .movie-meta {
        font-size: 14px;
        color: #e0e7ff;
        border-top: 1px solid rgba(0, 245, 255, 0.2);
        padding-top: 12px;
        font-weight: 600;
    }
    
    /* Latency badge */
    .latency-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.2) 0%, rgba(255, 0, 255, 0.2) 100%);
        color: #00f5ff;
        padding: 8px 20px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 15px;
        border: 1px solid rgba(0, 245, 255, 0.4);
        margin-bottom: 25px;
        letter-spacing: 0.5px;
    }
    
    /* Location badge */
    .location-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(255, 170, 0, 0.2) 0%, rgba(255, 0, 255, 0.2) 100%);
        color: #ffaa00;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid rgba(255, 170, 0, 0.4);
        margin-left: 10px;
        letter-spacing: 0.3px;
    }
    
    /* Radio button styling */
    .stRadio label {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    .stRadio div[role="radiogroup"] label {
        color: #ffffff !important;
    }
    
    .stRadio div[role="radiogroup"] label p {
        color: #ffffff !important;
    }
    
    /* Slider min/max values */
    .stSlider [data-testid="stTickBarMin"],
    .stSlider [data-testid="stTickBarMax"] {
        color: #ffffff !important;
    }
    
    .stSlider [data-testid="stTickBar"] div {
        color: #ffffff !important;
    }
    
    /* Label colors */
    label {
        color: #00f5ff !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Section headers */
    h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    
    /* Sidebar labels and text */
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: #ffffff !important;
    }
    
    /* Sidebar input text should also be black */
    [data-testid="stSidebar"] .stTextInput input {
        color: #000000 !important;
        background: rgba(255, 255, 255, 0.95) !important;
        font-weight: 600;
    }
    
    /* Error message styling */
    .stAlert {
        background: rgba(255, 0, 100, 0.15);
        border: 1px solid rgba(255, 0, 100, 0.4);
        border-radius: 12px;
        color: #ff6b9d;
    }
    
    /* Info box styling */
    .info-box {
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.1) 0%, rgba(255, 0, 255, 0.1) 100%);
        border: 1px solid rgba(0, 245, 255, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        color: #ffffff;
        font-size: 14px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 MovieMatch AI")
st.markdown("<p style='color: #b794f6; font-size: 18px; margin-top: -20px; font-weight: 500;'>Discover your next favorite movie powered by AI</p>", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Settings")
api_url = st.sidebar.text_input("API URL", "http://localhost:5000")
top_k = st.sidebar.slider("Number of Results", 3, 21, 12, step=3)
mode = st.sidebar.radio("Selection Mode", ["Existing User", "New User"])

# Helper function to extract region from zipcode
def get_region_name(zipcode):
    """Get region name from zipcode for display"""
    if not zipcode or len(zipcode) < 1:
        return None
    
    first_digit = zipcode[0]
    region_map = {
        '0': 'Northeast', '1': 'Northeast',
        '2': 'South', '3': 'South', '6': 'South', '7': 'South',
        '4': 'Midwest', '5': 'Midwest',
        '8': 'West', '9': 'West'
    }
    return region_map.get(first_digit, 'Other')


def display_movie_grid(movies):
    cols = st.columns(3)
    for idx, movie in enumerate(movies):
        # Handle genres - provide default if missing
        genres_str = movie.get('genres', 'Movie')
        if genres_str and genres_str != 'Movie':
            genres = genres_str.split('|')
        else:
            genres = ['Movie']
        
        genre_html = "".join([f'<span class="genre-tag">{g}</span>' for g in genres[:3]])
        
        # FIXED: Safely handle release_year
        release_year = movie.get('release_year', 'N/A')
        if release_year == 'N/A' or release_year is None or release_year == '':
            release_year = 'N/A'
        else:
            try:
                release_year = int(release_year)
            except (ValueError, TypeError):
                release_year = 'N/A'
        
        with cols[idx % 3]:
            st.markdown(f"""
                <div class="movie-card">
                    <div>
                        <div class="movie-title">{movie['title']}</div>
                        <div class="movie-year">📅 {release_year}</div>
                        <div style="margin-top: 10px;">{genre_html}</div>
                    </div>
                    <div class="movie-meta">
                        ⭐ <b>{movie['avg_rating']}</b> &nbsp; | &nbsp; 👥 {movie['num_ratings']:,} ratings
                    </div>
                </div>
            """, unsafe_allow_html=True)


# Main UI Logic
if mode == "Existing User":
    st.markdown("### 🎯 Get Personalized Recommendations")
    user_id = st.number_input("Enter Your User ID", 1, 6040, 1)
    
    if st.button("🚀 Generate Recommendations"):
        with st.spinner("Finding perfect movies for you..."):
            try:
                res = requests.post(f"{api_url}/recommend", json={"user_id": int(user_id), "top_k": top_k})
                if res.status_code == 200:
                    data = res.json()
                    st.markdown(f'<div class="latency-badge">⚡ Generated in {data["latency_ms"]}ms</div>', unsafe_allow_html=True)
                    display_movie_grid(data['recommendations'])
                else:
                    st.error(f"Error: {res.status_code} - {res.text}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection Error: Cannot connect to the API server. Make sure Flask app is running at " + api_url)
            except Exception as e: 
                st.error(f"❌ Error: {str(e)}")

else:
    st.markdown("### ✨ Tell Us About Yourself")
    
    # Info box explaining zipcode feature
    st.markdown("""
        <div class="info-box">
            💡 <b>New!</b> Add your zipcode for location-aware recommendations. 
            We'll blend movies popular in your region with those matching your demographics.
        </div>
    """, unsafe_allow_html=True)
    
    # Demographics inputs
    c1, c2, c3 = st.columns(3)
    with c1: 
        gender = st.selectbox("Gender", ["M", "F"])
    with c2: 
        age = st.select_slider("Age Group", options=[1, 18, 25, 35, 45, 50, 56])
    with c3: 
        occ = st.number_input("Occupation ID", 0, 20, 0)
    
    # Zipcode input
    zipcode = st.text_input(
        "📍 Zipcode (Optional)", 
        placeholder="e.g., 90210, 10001, 60601",
        max_chars=5,
        help="US zipcode for location-aware recommendations. Leave empty for demographic-only matching."
    )
    
    # Show region detection
    if zipcode and zipcode.strip():
        region = get_region_name(zipcode.strip())
        if region and region != 'Other':
            st.markdown(f'<span class="location-badge">📍 {region} Region Detected</span>', unsafe_allow_html=True)
        elif region == 'Other':
            st.warning("⚠️ Zipcode not recognized. We'll use demographic matching only.")
    
    if st.button("🎬 Discover Movies"):
        with st.spinner("Curating movies just for you..."):
            try:
                # Build demographics payload
                demographics = {
                    "gender": gender, 
                    "age": age, 
                    "occupation": occ
                }
                
                # Add zipcode if provided and valid
                if zipcode and zipcode.strip():
                    demographics["zipcode"] = zipcode.strip()
                
                payload = {
                    "demographics": demographics, 
                    "top_k": top_k
                }
                
                res = requests.post(f"{api_url}/recommend/new-user", json=payload)
                
                if res.status_code == 200:
                    data = res.json()
                    
                    # Show latency badge
                    latency_html = f'<div class="latency-badge">⚡ Generated in {data["latency_ms"]}ms</div>'
                    
                    # Show location info if zipcode was used
                    if zipcode and zipcode.strip():
                        region = get_region_name(zipcode.strip())
                        if region and region != 'Other':
                            latency_html += f'<span class="location-badge">📍 Using {region} preferences</span>'
                    
                    st.markdown(latency_html, unsafe_allow_html=True)
                    
                    # Display recommendations
                    display_movie_grid(data['recommendations'])
                    
                    # Show helpful tip
                    if not zipcode or not zipcode.strip():
                        st.info("💡 Tip: Add your zipcode above to get region-specific recommendations!")
                else:
                    st.error(f"Error: {res.status_code} - {res.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection Error: Cannot connect to the API server. Make sure Flask app is running at " + api_url)
            except Exception as e: 
                st.error(f"❌ Error: {str(e)}")


# Footer with instructions
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #b794f6; font-size: 14px; padding: 20px;'>
        <b>How it works:</b><br>
        🎯 <b>Existing User:</b> Get personalized recommendations based on your watch history<br>
        ✨ <b>New User:</b> Get recommendations based on demographics (+ location if zipcode provided)<br>
        📍 <b>Location Bonus:</b> Add zipcode for region-specific movie preferences
    </div>
""", unsafe_allow_html=True)