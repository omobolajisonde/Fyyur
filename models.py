from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy();


def setup_db(app):
    db.init_app(app)
    return db


class Venue(db.Model):
    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    website_link = db.Column(db.String(500))
    searching_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String())
    shows = db.relationship(
        "Show", backref="venues", lazy=False, cascade="all, delete-orphan"
    )


class Artist(db.Model):
    __tablename__ = "artists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    searching_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String())
    shows = db.relationship(
        "Show", backref="artists", lazy=False, cascade="all, delete-orphan"
    )


class Show(db.Model):
    __tablename__ = "shows"

    artist_id = db.Column(db.Integer, db.ForeignKey(
        "artists.id"), primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        "venues.id"), primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Artist ID: {self.artist_id}>, <Venue ID: {self.venue_id}>, <Start Time: {self.start_time}> \n"
