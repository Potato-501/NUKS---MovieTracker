from flask import Blueprint, request, jsonify
from extensions import db
from models import Movie
import requests

# Blueprint for movie service
movieService_bp = Blueprint("movieService", __name__)



### ROUTE FOR OMBDb API - Fetch movie details by title ###
@movieService_bp.route("/search", methods=["GET"])
def search_movies():
    query = request.args.get("query")
    if not query:
        return {"error": "Please provide a movie title"}, 400
    

    # Parametri za OMDb API klic.
    params = {
        's': query,
        'apikey': '37808c24'
    }
    url = "http://www.omdbapi.com/"


    # Make the request to the OMDb API
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"error": "Failed to fetch data from OMDb API"}, 500
    data = response.json()
    if data.get("Response") == "False":
        return {"error": data.get("Error", "Movie not found")}, 404
    

    # Tukaj dobimo vse rezultate iskanja, ki jih vrne OMDb API
    raw_results = data.get("Search", [])

    # Filtiramo podatke iz raw_results, samo tiste ki nas zanimajo
    results = [
        {
            "title": movie.get("Title"),
            "year": movie.get("Year"),
            "poster_url": movie.get("Poster") if movie.get("Poster") != "N/A" else None,
        }
        for movie in raw_results
    ]

    return jsonify(results)



### ROUTE FOR ADDING A MOVIE FROM SEARCH RESULTS ###
@movieService_bp.route("/add", methods=["POST"])
def add_movie_from_search():
    data = request.get_json()
    
    title_input = data.get("title", "").strip()
    year_input = data.get("year", "").strip()

    if not title_input:
        return {"error": "Title is required"}, 400


    new_movie = Movie(title=title_input, year=year_input)

    try:
        db.session.add(new_movie)
        db.session.commit()
        return jsonify({"message": "Added!"}), 201
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500



### GET METHOD - Retrieve all movies ###
@movieService_bp.route("/", methods=["GET"])
def get_movies():
    # Query all movies from the database
    all_movies = Movie.query.all()

    # Convert SQLAlchemy objects into a list of dictionaries for JSON
    results = [
        {
            "id": m.id,
            "title": m.title,
            "status": m.status,
            "year": m.year,
            "poster_url": m.poster_url,
        }
        for m in all_movies
    ]
    return jsonify(results)



### POST METHOD - Add a new movie ###
@movieService_bp.route("/", methods=["POST"])
def add_movie():
    data = request.get_json()

    if not data or "title" not in data:
        return {"error": "Missing title"}, 400

    # Create a new Movie instance
    new_movie = Movie(
        title=data.get("title"),
        status=data.get("status", "want to watch"),
        year=data.get("year"),
        poster_url=data.get("poster_url"),
    )

    # Add to session and commit to save to the .db file
    db.session.add(new_movie)
    db.session.commit()

    return jsonify(
        {
            "id": new_movie.id,
            "title": new_movie.title,
            "status": new_movie.status,
            "year": new_movie.year,
            "poster_url": new_movie.poster_url,
        }
    ), 201



### PUT METHOD - Update an existing movie ###
@movieService_bp.route("/<int:movie_id>", methods=["PUT"])
def update_movie(movie_id):
    data = request.get_json()

    # Find the movie by primary key
    movie = Movie.query.get(movie_id)

    if not movie:
        return {"error": "Movie not found"}, 404

    # Update fields if they exist in the request
    movie.title = data.get("title", movie.title)
    movie.status = data.get("status", movie.status)
    movie.year = data.get("year", movie.year)
    movie.poster_url = data.get("poster_url", movie.poster_url)

    db.session.commit()

    return jsonify(
        {
            "id": movie.id,
            "title": movie.title,
            "status": movie.status,
            "year": movie.year,
            "poster_url": movie.poster_url,
        }
    )



### DELETE METHOD - Remove a movie ###
@movieService_bp.route("/<int:movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    movie = Movie.query.get(movie_id)

    if not movie:
        return {"error": "Movie not found"}, 404

    db.session.delete(movie)
    db.session.commit()

    return {"message": f"Movie {movie_id} deleted"}, 200
