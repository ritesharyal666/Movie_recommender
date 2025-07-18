import streamlit as st
import pickle
import requests
import gdown
from dotenv import load_dotenv
import os
from PIL import Image
import io
import time

# Configuration
load_dotenv()
TMDB_API_KEY = os.getenv('TMDB_API_KEY_')
TMDB_API_URL = "https://api.themoviedb.org/3"
POSTER_SIZE = "w500"  # Best quality that fits well
CACHE_EXPIRATION = 86400  # 24 hours cache

# Custom CSS for perfect styling
st.markdown("""
<style>
.movie-card {
    border-radius: 10px;
    padding: 10px;
    transition: transform 0.2s;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.movie-card:hover {
    transform: scale(1.03);
}
.poster-container {
    width: 100%;
    aspect-ratio: 2/3;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    border-radius: 8px;
    background-color: #f0f2f6;
}
.poster-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.movie-title {
    margin-top: 8px;
    font-weight: 600;
    font-size: 14px;
    text-align: center;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 40px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource(ttl=CACHE_EXPIRATION)
def download_file_from_drive(file_url, output_path):
    file_id = file_url.split('/d/')[1].split('/')[0]
    gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=True)
    return output_path

@st.cache_resource(ttl=CACHE_EXPIRATION)
def load_data():
    movies_file_url = "https://drive.google.com/file/d/1d7mhUo4SzR45fSYi-tFQR741GYj9NmYw/view?usp=sharing"
    similarity_file_url = "https://drive.google.com/file/d/1a10EQd5ml0DW7iy85YYmKL1OXNZpW1yy/view?usp=sharing"
    
    movies_pkl_path = download_file_from_drive(movies_file_url, "movies.pkl")
    similarity_pkl_path = download_file_from_drive(similarity_file_url, "similarity.pkl")
    
    return (
        pickle.load(open(movies_pkl_path, 'rb')),
        pickle.load(open(similarity_pkl_path, 'rb'))
    )

@st.cache_data(ttl=CACHE_EXPIRATION, show_spinner=False)
def fetch_movie_poster(movie_name):
    try:
        search_url = f"{TMDB_API_URL}/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['results']:
            poster_path = data['results'][0].get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/{POSTER_SIZE}{poster_path}"
        return None
    except Exception:
        return None

def movie_card(title, poster_url):
    """Custom movie card component with perfect styling"""
    card_html = f"""
    <div class="movie-card">
        <div class="poster-container">
            <img src="{poster_url if poster_url else 'https://via.placeholder.com/300x450?text=No+Poster'}" 
                 class="poster-img" 
                 alt="{title}"
                 onerror="this.src='https://via.placeholder.com/300x450?text=Poster+Not+Available'">
        </div>
        <div class="movie-title" title="{title}">{title}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="Movie Recommender", page_icon="🎬")
    
    st.title("🎬 Movie Recommendation Engine")
    st.markdown("Discover films similar to your favorites with perfect visual presentation")
    
    with st.spinner('Loading movie database...'):
        choosen_df, similarity_matrix = load_data()
    
    if 'title' not in choosen_df.columns:
        st.error("Invalid data format: Missing 'title' column")
        return
    
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        selected_movie = st.selectbox(
            "Select a movie:",
            choosen_df['title'].values,
            index=0,
            help="Search for a movie to get recommendations"
        )
        
        if st.button('Get Recommendations', type="primary", use_container_width=True):
            st.session_state.show_recs = True
    
    if st.session_state.get('show_recs', False):
        with st.spinner(f'Finding similar movies to "{selected_movie}"...'):
            try:
                movie_index = choosen_df[choosen_df['title'] == selected_movie].index[0]
                distances = similarity_matrix[movie_index]
                movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:31]
                
                st.subheader(f"Movies Similar to: {selected_movie}")
                st.divider()
                
                # Display 5 movies per row
                cols_per_row = 5
                for i in range(0, len(movies_list), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        if i + j < len(movies_list):
                            with cols[j]:
                                movie_title = choosen_df.iloc[movies_list[i+j][0]].title
                                poster_url = fetch_movie_poster(movie_title)
                                movie_card(movie_title, poster_url)
            
            except Exception as e:
                st.error(f"Error generating recommendations: {str(e)}")

if __name__ == "__main__":
    main()
