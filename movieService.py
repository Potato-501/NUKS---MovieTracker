from flask import Blueprint, request, jsonify, Response, session
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import Movie
import requests
import os
from posterStorageService import upload_poster_from_url, delete_poster, fetch_poster_bytes


# Blueprint for movie service - vsa ta koda se potem inicializira v main.py
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

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in to save movies."}), 401

    data = request.get_json()
    
    title_input = data.get("title", "").strip()
    year_input = data.get("year", "").strip()
    status_input = data.get("status", "watchlist").strip().lower()
    external_poster_url = data.get("poster_url")

    # Stvari za poster-je (me je FUL jebalu)
    poster_url_input = None
    if external_poster_url:
        external_poster_url = external_poster_url.strip()
        # Ignore OMDb placeholder values like "N/A" and empty strings
        if external_poster_url and external_poster_url.upper() != "N/A":
            try:
                poster_url_input = upload_poster_from_url(external_poster_url)
            except Exception as e:
                # If we can't download/upload the image, fall back to using the external URL so frontend can display it
                poster_url_input = external_poster_url

    if not title_input:
        return {"error": "Title is required"}, 400

    if not status_input:
        return {"error": "Status is required"}, 400

    try:
        existing_movie = Movie.query.filter_by(user_id=user_id, title=title_input).first()

        if existing_movie:
            movie = existing_movie
            movie.year = year_input or movie.year
            movie.status = status_input
            if poster_url_input:
                movie.poster_url = poster_url_input
            message = f"Updated movie {movie.title}"
        else:
            movie = Movie(
                user_id=user_id,
                title=title_input,
                year=year_input,
                status=status_input,
                poster_url=poster_url_input,
            )
            db.session.add(movie)
            message = f"Added movie {movie.title}"

        db.session.commit()
        return jsonify({"message": f"{message} to {status_input}", "poster_url": movie.poster_url}), 201
    except IntegrityError:
        db.session.rollback()
        return {"error": "Movie with this title is already in your database"}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500



### Route to Get All Movies in the Database ###
@movieService_bp.route("/", methods=["GET"])
def get_all_movies():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in to view movies."}), 401

    movies = Movie.query.filter_by(user_id=user_id).all()
    movies_list = [m.to_dict() for m in movies]
    return jsonify(movies_list)


### Route to Proxy Poster URL for Frontend Rendering ###
@movieService_bp.route("/poster", methods=["GET"])
def proxy_poster():
    poster_url = request.args.get("url", "").strip()
    if not poster_url:
        return jsonify({"error": "Missing poster url"}), 400

    if not poster_url.lower().startswith(("http://", "https://")):
        return jsonify({"error": "Invalid poster url"}), 400

    try:
        content, content_type = fetch_poster_bytes(poster_url)
        return Response(content, mimetype=content_type)
    except Exception as e:
        return jsonify({"error": f"Failed to load poster: {str(e)}"}), 502



### Route to Update Movie Status ###
@movieService_bp.route("/<int:movie_id>/status", methods=["PUT"])
def update_status(movie_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in to update movies."}), 401

    data = request.get_json()
    movie = Movie.query.filter_by(id=movie_id, user_id=user_id).first_or_404()
    
    # We expect {'status': 'library'}
    movie.status = data.get('status', movie.status)
    db.session.commit()
    return jsonify({"message": "Status updated!"})



### Route to Delete a Movie from the library ###
@movieService_bp.route("/<int:movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in to delete movies."}), 401

    movie = Movie.query.filter_by(id=movie_id, user_id=user_id).first_or_404()
    db.session.delete(movie)
    db.session.commit()
    delete_poster(movie.poster_url)
    return jsonify({"message": "Movie deleted!"})



### Route to Update Movie Rating ###
@movieService_bp.route("/<int:movie_id>/rating", methods=["PATCH"])
def update_rating(movie_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in to rate movies."}), 401

    data = request.get_json()
    movie = Movie.query.filter_by(id=movie_id, user_id=user_id).first_or_404()
    movie.rating = data.get('rating')
    db.session.commit()
    return jsonify({"message": "Rating updated"})