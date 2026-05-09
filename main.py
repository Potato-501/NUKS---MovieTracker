from flask import Flask
from flask_cors import CORS
from extensions import db, mongo
from models import Movie
from movieService import movieService_bp
from reviewService import review_bp
from dotenv import load_dotenv

# # Load environment variables from .env file
load_dotenv()

# Create Flash app
def create_app():
    app = Flask(__name__)


    # SQL Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'   # Povemo, da bomo uporabljal SQLite bazo z imenom movies.db
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False            # Izklopimo sledenje spremembam, ker ni potrebno in lahko povzroči dodatno porabo pomnilnika


    # MongoDB configuration
    app.config["MONGO_URI"] = "mongodb://localhost:27017/movieDB"
    mongo.init_app(app)


    # Povežemo SQLAlchemy z našo Flask aplikacijo (db objekt je it extensions.py)
    db.init_app(app)    


    # Register Blueprints
    app.register_blueprint(movieService_bp, url_prefix='/movies')
    app.register_blueprint(review_bp, url_prefix='/api/reviews')

    # Enable CORS for the app - omogoča, da lahko frontend komunicira z backend 
    CORS(app)

    
    # Homepage route
    @app.route("/")
    def home():
        return """
        <h1>Movie Tracker</h1>
        <p>Movie tracker is up and operational!</p>
        <button onclick="location.href='/movies'" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">
            Go to Movies
        </button>
        """
        
    return app


# Run the app    
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

    with app.app_context():
        print("Checking if SQL tables exist...")
        db.create_all()  # This creates the movies.db file and all tables defined in models.py
        print("SQL Tables verified!")