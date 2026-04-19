from flask import Flask
from extensions import db
from models import Movie  # Import models so SQLAlchemy "sees" the tables
from movieService import movieService_bp

def create_app():
    app = Flask(__name__)


    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'   # Povemo, da bomo uporabljal SQLite bazo z imenom movies.db
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False            # Izklopimo sledenje spremembam, ker ni potrebno in lahko povzroči dodatno porabo pomnilnika


    # Povežemo SQLAlchemy z našo Flask aplikacijo (db objekt je it extensions.py)
    db.init_app(app)    


    # Register Blueprints
    app.register_blueprint(movieService_bp, url_prefix='/movies')


    # Home route (homepage)
    @app.route("/")
    def home():
        return """
        <h1>Movie Tracker</h1>
        <p>Movie tracker is up and operational!</p>
        <button onclick="location.href='/movies'" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">
            Go to Movies
        </button>
        """

    # Create tables (ko se aplikacija zažene, preverimo, če tabele obstajajo, če ne, jih ustvarimo)
    with app.app_context():
        db.create_all()
        
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
