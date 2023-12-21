from fastapi import FastAPI
import pandas as pd
import pickle
import numpy as np
from pydantic import BaseModel
from urllib.parse import unquote

app = FastAPI()
# Create a Pydantic model to define the request body
class BookRequest(BaseModel):
    title: str

# Import your model, preprocessors, etc.
model = pickle.load(open('artifacts/model.pkl', 'rb'))
books_title = pickle.load(open('artifacts/books_title.pkl', 'rb'))
final_rating = pickle.load(open('artifacts/final_rating.pkl', 'rb'))
book_pivot_table = pickle.load(open('artifacts/book_pivot_table.pkl', 'rb'))

# ========= API ENDPOINT ==============
@app.get("/")
def read_root():
    return {"message": "Books Recommendation!"}

# GET ALL BOOKS DATA
@app.get("/books")
async def books_data():
    return {
        "data": final_rating.head(50).values.tolist()
    }

# GET DETAIL OF A BOOK
@app.get("/details/{isbn}")
async def detail_book(isbn: str):
    data = isbn
    details = final_rating.loc[final_rating.ISBN == data].to_numpy()[0]
    return {
        "data": details.tolist()
        }


# GET RANDOM BOOKS
@app.get("/today-picks")
async def today_picks():
    random = final_rating.sample(10)
    return {
        "data": random.values.tolist(),
    }

# GET RECOMMENDATION
## function fetch_poster
def fetch_poster(suggestion):
    book_title = []
    ids_index = []
    poster_url = []

    for book_id in suggestion:
        book_title.append(book_pivot_table.index[book_id])
    
    for i in book_title[0]:
        ids = np.where(final_rating['title'] == i)[0][0]
        ids_index.append(ids)
    
    for idx in ids_index:
        url = final_rating.iloc[idx]['image_url']
        poster_url.append(url)
    
    return poster_url

## function recommend_books
def recommend_books(book_title):
     tmp = []
     book_list = []
     
     book_id = np.where(book_pivot_table.index == book_title)[0][0]
     distance, suggestion = model.kneighbors(book_pivot_table.iloc[book_id, :].values.reshape(1, -1), n_neighbors=10)

     poster_url = fetch_poster(suggestion)

     count = 1
     for i in range(len(suggestion)):
         books = book_pivot_table.index[suggestion[i]]
         for j in books:
             details = final_rating.loc[final_rating.title == j].to_numpy()[0]
             book_list.append(details.tolist())

     return book_list, poster_url 

## get recommendation
@app.get("/recommendations/{judul}")
async def get_recommendation(judul: str):
    judul_string = unquote(judul)
    title = judul_string
    recommended_books, poster_url = recommend_books(title)
    return {
            "data" : [recommended_books, poster_url]
            }

# GET RECOMMENDATION FROM LARGEST NUM_OF_RATING
@app.get("/user-choices")
async def user_choices():
    values = final_rating.nlargest(1, 'num_of_rating')
    title = values.iloc[0, 3]

    recommended_books, poster_url = recommend_books(title)
    return {
        "data": [recommended_books, poster_url]
        }