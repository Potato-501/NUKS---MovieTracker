from extensions import db

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    status = db.Column(db.String(20), default="watchlist")
    year = db.Column(db.String(4))
    poster_url = db.Column(db.String(255))
    rating = db.Column(db.Integer, default=0)