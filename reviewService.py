from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from datetime import datetime
from extensions import mongo

# Blueprint for written notes (reviews) - vsa ta koda se potem inicializira v main.py
review_bp = Blueprint('review_bp', __name__)

# Route to fetch the note for a specific movie ID
@review_bp.route('/<int:movie_id>', methods=['GET'])
def get_notes(movie_id):
    """Fetch the written note for a specific SQL movie ID."""
    note_data = mongo.db.movie_notes.find_one({"movie_id": movie_id})
    if note_data:
        return jsonify({
            "note": note_data['note'],
            "last_updated": note_data.get('last_updated')
        }), 200
    return jsonify({"note": ""}), 200


# Route to create or update a note for a specific movie ID
@review_bp.route('/<int:movie_id>', methods=['POST'])
def save_note(movie_id):
    """Create or update a note for a specific SQL movie ID."""
    data = request.get_json()
    note_text = data.get('note', '')

    mongo.db.movie_notes.update_one(
        {"movie_id": movie_id},
        {"$set": {
            "note": note_text,
            "last_updated": datetime.utcnow()
        }},
        upsert=True 
    )
    return jsonify({"message": "Note synced to MongoDB"}), 201


# Route to delete a note for a specific movie ID
@review_bp.route('/<int:movie_id>', methods=['DELETE'])
def delete_note(movie_id):
    """Wipe the note from Mongo without touching the SQL movie record."""
    mongo.db.movie_notes.delete_one({"movie_id": movie_id})
    return jsonify({"message": "Note deleted"}), 200