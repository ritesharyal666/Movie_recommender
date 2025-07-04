import streamlit as st
import pickle
import requests
import gdown

from dotenv import load_dotenv
import os

load_dotenv()

TMDB_API_KEY_ = os.getenv('TMDB_API_KEY')

# Download the .pkl files from Google Drive
def download_file_from_drive(file_url, output_path):
    # Extract file ID from the Google Drive link
    file_id = file_url.split('/d/')[1].split('/')[0]
    gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)

# File URLs from Google Drive
movies_file_url = "https://drive.google.com/file/d/1d7mhUo4SzR45fSYi-tFQR741GYj9NmYw/view?usp=sharing"
similarity_file_url = "https://drive.google.com/file/d/1a10EQd5ml0DW7iy85YYmKL1OXNZpW1yy/view?usp=sharing"

# Download the .pkl files
movies_file_path = "movies.pkl"
similarity_file_path = "similarity.pkl"

download_file_from_drive(movies_file_url, movies_file_path)
download_file_from_drive(similarity_file_url, similarity_file_path)

# Load the DataFrame and similarity matrix
choosen_df = pickle.load(open(movies_file_path, 'rb'))  # Load the DataFrame
similarity_matrix = pickle.load(open(similarity_file_path, 'rb'))  # Load the similarity matrix

TMDB_API_KEY = TMDB_API_KEY_  # Your API key here
TMDB_API_URL = "https://api.themoviedb.org/3"

def fetch_movie_poster(movie_name):
    search_url = f"{TMDB_API_URL}/search/movie?api_key={TMDB_API_KEY}&query={movie_name}&language=en-US"
    response = requests.get(search_url).json()
    
    if response['results']:
        poster_path = response['results'][0].get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return None

def recommend(movie):
    try:
        movie_index = choosen_df[choosen_df['title'] == movie].index[0]
    except IndexError:
        return "Movie not found in the database."
    
    distances = similarity_matrix[movie_index]
    
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:31]
    
    recommended_movies = []
    recommended_movie_posters = []
    
    for i in movies_list:
        movie_title = choosen_df.iloc[i[0]].title
        poster_url = fetch_movie_poster(movie_title)
        recommended_movies.append(movie_title)
        recommended_movie_posters.append(poster_url)
    
    return recommended_movies, recommended_movie_posters

st.title("Movie Recommender System")

selected_movie = st.selectbox("Select a Movie", choosen_df['title'].values)

if selected_movie:
    st.subheader(f"Recommended movies similar to '{selected_movie}':")
    
    recommended_movies, recommended_movie_posters = recommend(selected_movie)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    for i in range(0, len(recommended_movies), 5):
        cols = [col1, col2, col3, col4, col5]
        for j in range(5):
            if i + j < len(recommended_movies):
                movie_title = recommended_movies[i + j]
                poster_url = recommended_movie_posters[i + j]
                cols[j].image(poster_url, width=150)
                cols[j].text(movie_title)
