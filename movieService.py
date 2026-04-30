from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import Movie
import requests
import os




# Blueprint for movie service
movieService_bp = Blueprint("movieService", __name__)



### Proxy Route to GET Movie Data from OMDb API ###
@movieService_bp.route("/search", methods=["GET"])
def proxy_search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    # Talk to OMDb API
    api_key = os.getenv("API_KEY") 
    response = requests.get(f"https://www.omdbapi.com/?s={query}&apikey={api_key}")

    # Return in Json format to frontend
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch data from OMDb API"}), response.status_code
    
  

### Route to Add a Movie from Search Results ###
@movieService_bp.route("/add", methods=["POST", "OPTIONS"])
def add_movie_from_search():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json()
    
    title_input = data.get("title", "").strip()
    year_input = data.get("year", "").strip()
    status_input = data.get("status").strip().lower()

    if not title_input:
        return {"error": "Title is required"}, 400

    if not status_input:
        return {"error": "Status is required"}, 400

    new_movie = Movie(title=title_input, year=year_input, status=status_input)

    try:
        db.session.add(new_movie)
        db.session.commit()
        return jsonify({"message": f"Added movie {new_movie.title} to {status_input}"}), 201
    except IntegrityError:
        db.session.rollback()
        return {"error": "Movie with this title is already in the database"}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500



### Route to Get All Movies in the Database ###
@movieService_bp.route("/", methods=["GET"])
def get_all_movies():
    movies = Movie.query.all()
    movies_list = [{"id": m.id, "title": m.title, "status": m.status, "year": m.year, "poster_url": m.poster_url, "rating": m.rating} for m in movies]
    return jsonify(movies_list)



### Route to Update Movie Status ###
@movieService_bp.route("/<int:movie_id>/status", methods=["PUT"])
def update_status(movie_id):
    data = request.get_json()
    movie = Movie.query.get_or_404(movie_id)
    
    # We expect {'status': 'library'}
    movie.status = data.get('status', movie.status)
    db.session.commit()
    return jsonify({"message": "Status updated!"})



### Route to Delete a Movie from the library ###
@movieService_bp.route("/<int:movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": "Movie deleted!"})



### Route to Update Movie Rating ###
@movieService_bp.route("/<int:movie_id>/rating", methods=["PATCH"])
def update_rating(movie_id):
    data = request.get_json()
    movie = Movie.query.get_or_404(movie_id)
    movie.rating = data.get('rating')
    db.session.commit()
    return jsonify({"message": "Rating updated"})