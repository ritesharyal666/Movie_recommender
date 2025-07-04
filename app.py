import streamlit as st
import pickle
import requests
import gdown
from dotenv import load_dotenv
import os

load_dotenv()

TMDB_API_KEY_ = os.getenv('TMDB_API_KEY_')

# Define file paths
movies_file_path = "movies.pkl"
similarity_file_path = "similarity.pkl"

def download_file_from_drive(file_id, output_path):
    # Check if the file already exists, if not, download it
    if not os.path.exists(output_path):
        gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)

# Download required files if they don't already exist
download_file_from_drive("1d7mhUo4SzR45fSYi-tFQR741GYj9NmYw", movies_file_path)
download_file_from_drive("1a10EQd5ml0DW7iy85YYmKL1OXNZpW1yy", similarity_file_path)

# Load the DataFrame and similarity matrix
choosen_df = pickle.load(open(movies_file_path, 'rb'))  # Load the DataFrame
similarity_matrix = pickle.load(open(similarity_file_path, 'rb'))  # Load the similarity matrix

TMDB_API_KEY = TMDB_API_KEY_  # Your API key here
TMDB_API_URL = "https://api.themoviedb.org/3"

def fetch_movie_poster(movie_name):
    # Fetch movie poster from TMDB API
    search_url = f"{TMDB_API_URL}/search/movie?api_key={TMDB_API_KEY}&query={movie_name}&language=en-US"
    response = requests.get(search_url).json()
    
    if response['results']:
        poster_path = response['results'][0].get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return "https://via.placeholder.com/150"  # Return a placeholder image if no poster is found

def recommend(movie):
    try:
        # Find the index of the selected movie in the dataset
        movie_index = choosen_df[choosen_df['title'] == movie].index[0]
    except IndexError:
        return "Movie not found in the database.", []
    
    distances = similarity_matrix[movie_index]
    
    # Get the top 30 most similar movies (excluding the movie itself)
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:31]
    
    recommended_movies = []
    recommended_movie_posters = []
    
    for i in movies_list:
        movie_title = choosen_df.iloc[i[0]].title
        poster_url = fetch_movie_poster(movie_title)
        recommended_movies.append(movie_title)
        recommended_movie_posters.append(poster_url)
    
    return recommended_movies, recommended_movie_posters

# Streamlit UI
st.title("Movie Recommender System")

# Select a movie
selected_movie = st.selectbox("Select a Movie", choosen_df['title'].values)

if selected_movie:
    st.subheader(f"Recommended movies similar to '{selected_movie}':")
    
    recommended_movies, recommended_movie_posters = recommend(selected_movie)
    
    # Display the recommended movies in 5 columns
    col1, col2, col3, col4, col5 = st.columns(5)
    for i in range(0, len(recommended_movies), 5):
        cols = [col1, col2, col3, col4, col5]
        for j in range(5):
            if i + j < len(recommended_movies):
                movie_title = recommended_movies[i + j]
                poster_url = recommended_movie_posters[i + j]
                cols[j].image(poster_url, width=150)
                cols[j].text(movie_title)
