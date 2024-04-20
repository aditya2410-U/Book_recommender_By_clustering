from flask import Flask, request, jsonify, render_template
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

# Load and preprocess the data
books = pd.read_csv('BX-Books.csv', sep=";", encoding='latin-1', on_bad_lines='skip')
books = books[['ISBN', 'Book-Title', 'Book-Author', 'Year-Of-Publication', 'Publisher']]
books.rename(columns={'Book-Title':'title', 'Book-Author':'author', 'Year-Of-Publication':'year', 'Publisher':'publisher'}, inplace=True)

ratings = pd.read_csv('BX-Book-Ratings.csv', sep=';', encoding='latin-1')
ratings.rename(columns={'User-ID':'user_id', 'Book-Rating':'rating'}, inplace=True)

x = ratings['user_id'].value_counts() > 200
y = x[x].index
ratings = ratings[ratings['user_id'].isin(y)]

books_with_ratings = ratings.merge(books, on='ISBN')
number_rating = books_with_ratings.groupby('title')['rating'].count().reset_index()
number_rating.rename(columns={'rating':'number of rating'}, inplace=True)
final_rating = books_with_ratings.merge(number_rating, on='title')
final_rating = final_rating[final_rating['number of rating'] >= 50]
final_rating.drop_duplicates(['user_id','title'], inplace=True)
book_pivot = final_rating.pivot_table(columns='user_id', index='title', values='rating')
book_pivot.fillna(0, inplace=True)
book_sparse = csr_matrix(book_pivot)

# Train the model
model = NearestNeighbors(algorithm='brute')
model.fit(book_sparse)

# Function to recommend books
def recommend_book(book_name):
    book_id = np.where(book_pivot.index == book_name)[0][0]
    distances, suggestions = model.kneighbors(book_pivot.iloc[book_id,:].values.reshape(1,-1), n_neighbors=6)
    recommended_books = [book_pivot.index[suggestion] for suggestion in suggestions]
    return recommended_books

# Flask app
app = Flask(__name__)

# Frontend route
@app.route('/')
def index():
    return render_template('index.html')

# Recommendation endpoint
@app.route('/recommend', methods=['POST'])
def get_recommendations():
    data = request.json
    book_name = data.get('bookName')
    recommendations = recommend_book(book_name)
    # Convert the recommendations from Index object to a list
    recommendations_list = recommendations[0].tolist()
    return jsonify({'recommendations': recommendations_list})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
