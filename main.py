from flask import Flask, send_from_directory
from flask_cors import CORS
from extensions import db, mongo
from movieService import movieService_bp
from reviewService import review_bp
from authService import auth_bp
from dotenv import load_dotenv
import os

# # Load environment variables from .env file
load_dotenv()

# Create Flash app
def create_app():
    app = Flask(__name__, static_folder=".", static_url_path="")
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///movies.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config["MONGO_URI"] = "mongodb://localhost:27017/movieDB"
    mongo.init_app(app)

    db.init_app(app)

    app.register_blueprint(movieService_bp, url_prefix='/movies')
    app.register_blueprint(review_bp, url_prefix='/api/reviews')
    app.register_blueprint(auth_bp)

    CORS(app, supports_credentials=True)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return send_from_directory(app.static_folder, 'index.html')

    return app


# Run the app    
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
