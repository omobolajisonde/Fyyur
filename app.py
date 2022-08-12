# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    abort,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

from flask_migrate import Migrate

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
from models import *

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Helper Functions.
# ----------------------------------------------------------------------------#

# This function helps construct error msgs using data from form.errors

def error_msg_constructor(error_dict):
    error_msg = ""
    keys = list(error_dict.keys())
    values = list(error_dict.values())
    for i in range(len(error_dict)):
        if (i+1) == len(error_dict):
            error_msg = error_msg + values[i][0] + " for " + keys[i] + "."
            continue
        if (i+2) == len(error_dict):
            error_msg = error_msg + \
                values[i][0] + " for " + keys[i] + " and "
            continue
        error_msg = error_msg + values[i][0] + " for " + keys[i] + ", "
    return error_msg


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    distinct_venues = (
        Venue.query.with_entities(Venue.city, Venue.state)
        .group_by(Venue.city, Venue.state)
        .all()
    )  # returns a list of 2-item tuples
    for dv in distinct_venues:
        location_data = {"city": dv[0], "state": dv[1]}
        venues = Venue.query.filter_by(city=dv[0], state=dv[1]).all()
        venues_data = []
        for venue in venues:
            venue_obj = {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(
                    list(
                        filter(
                            lambda showRow: showRow.start_time > datetime.now(),
                            venue.shows,
                        ) # filters out past shows form venue.shows
                    )
                ),
            }
            venues_data.append(venue_obj)

        location_data["venues"] = venues_data
        data.append(location_data)

    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_query = request.form.get("search_term", "")
    search_results = Venue.query.filter(
        Venue.name.ilike("%{}%".format(search_query))).all() # Queries row(s) from venues table with name fully or partially matching search_query
    response = {
        "count": len(search_results)
    }
    data = []
    for result in search_results:
        result_data = {
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": len(list(filter(lambda show: show.start_time > datetime.now(), result.shows))), # filters out past shows form venue.shows
        }
        data.append(result_data)
    response["data"] = data
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(", "),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.searching_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }

    # GETTING PAST SHOWS FOR THE CURRENT VENUE
    past_shows_results = filter(
        lambda show: show.start_time < datetime.now(), venue.shows 
    )
    past_shows = []
    for past_show in past_shows_results:
        artist = Artist.query.get(past_show.artist_id)
        past_show_data = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(past_show.start_time),
        }
        past_shows.append(past_show_data)
    data["past_shows"] = past_shows
    data["past_shows_count"] = len(past_shows)

    # GETTING UPCOMING SHOWS FOR THE CURRENT VENUE
    upcoming_shows_results = filter(
        lambda show: show.start_time > datetime.now(), venue.shows
    )
    upcoming_shows = []
    for up_show in upcoming_shows_results:
        artist = Artist.query.get(up_show.artist_id)
        up_show_data = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(up_show.start_time),
        }
        upcoming_shows.append(up_show_data)
    data["upcoming_shows"] = upcoming_shows
    data["upcoming_shows_count"] = len(upcoming_shows)
    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    form = VenueForm(request.form)
    if form.validate():
        error = False
        try:
            name = form.name.data
            city = form.city.data
            state = form.state.data
            address = form.address.data
            phone = form.phone.data
            image_link = form.image_link.data
            facebook_link = form.facebook_link.data
            genres = ", ".join(form.genres.data)
            website_link = form.website_link.data
            searching_talent = form.seeking_talent.data
            seeking_description = form.seeking_description.data

            venue = Venue(
                name=name,
                city=city,
                state=state,
                address=address,
                phone=phone,
                image_link=image_link,
                facebook_link=facebook_link,
                genres=genres,
                website_link=website_link,
                searching_talent=searching_talent,
                seeking_description=seeking_description,
            )
            db.session.add(venue)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            # on unsuccessful db insert, flash error.
            flash(
                f"An error occurred. Venue, \"{form.name.data}\" could not be listed.", "error")
            abort(500)
        else:
            # on successful db insert, flash success
            flash(f"Venue, \"{request.form['name']}\" was successfully listed!")
            return redirect(url_for("venues"))
            # return render_template('pages/home.html')
    else:
        error_msg = error_msg_constructor(form.errors)
        flash(
            f"Venue, \"{form.name.data}\" could not be listed. An error occurred ({error_msg})", "error")
        return render_template("forms/new_venue.html", form=form)


@app.route("/venues/<venue_id>", methods=["POST"])
def delete_venue(venue_id):
    error = None
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash(
            f"An error occured. Venue, \"{venue.name}\" could not be deleted", 'error')
        abort(500)
    else:
        flash(f"Venue, \"{venue.name}\" was successfully deleted.")
        return redirect(url_for("index"))

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------


@app.route("/artists")
def artists():
    artists = Artist.query.all()
    data = []
    for artist in artists:
        artist_data = {
            "id": artist.id,
            "name": artist.name,
        }
        data.append(artist_data)
    data.reverse()
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_query = request.form.get("search_term", "")
    search_results = Artist.query.filter(
        Artist.name.ilike("%{}%".format(search_query))).all() # Queries row(s) from Artist table with name fully or partially matching search_query
    response = {
        "count": len(search_results)
    }
    data = []
    for result in search_results:
        result_data = {
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": len(list(filter(lambda show: show.start_time > datetime.now(), result.shows))), # filters out past shows
        }
        data.append(result_data)
    response["data"] = data

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get(artist_id)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(", "),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.searching_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
    }

    # GETTING PAST SHOWS FOR THE CURRENT ARTIST
    past_shows_results = filter(
        lambda show: show.start_time < datetime.now(), artist.shows
    )
    past_shows = []
    for past_show in past_shows_results:
        venue = Venue.query.get(past_show.venue_id)
        past_show_data = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": str(past_show.start_time),
        }
        past_shows.append(past_show_data)
    data["past_shows"] = past_shows
    data["past_shows_count"] = len(past_shows)

    # GETTING UPCOMING SHOWS FOR THE CURRENT VENUE
    upcoming_shows_results = filter(
        lambda show: show.start_time > datetime.now(), artist.shows
    )
    upcoming_shows = []
    for up_show in upcoming_shows_results:
        venue = Venue.query.get(up_show.venue_id)

        up_show_data = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": str(up_show.start_time),
        }
        upcoming_shows.append(up_show_data)
    data["upcoming_shows"] = upcoming_shows
    data["upcoming_shows_count"] = len(upcoming_shows)
    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    form.genres.data = artist.genres.split(", ")  # splitting back in to a list
    form.state.data = artist.state
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(", "),  # splitting back in to a list
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.searching_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
    }

    return render_template("forms/edit_artist.html", form=form, artist=data)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form)

    if form.validate():
        error = None
        try:
            artist = Artist.query.get(artist_id)
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.image_link = form.image_link.data
            artist.facebook_link = form.facebook_link.data
            artist.genres = ", ".join(form.genres.data)
            artist.website_link = form.website_link.data
            artist.searching_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data

            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            flash(
                f"An error occurred. Artist, \"{form.name.data}\", info could not be updated. Please try again!", "error")
            abort(500)
        else:
            # on successful db insert, flash success
            flash(form.name.data + ", your info was successfully updated!")
            return redirect(url_for("show_artist", artist_id=artist_id))
    else:
        artist = Artist.query.get(artist_id)
        error_msg = error_msg_constructor(form.errors)
        flash(
            f"Artist, \"{form.name.data}\" info could not be updated. An error occurred ({error_msg})", "error")
        return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.genres.data = venue.genres.split(", ") # split each genre back to a list
    form.state.data = venue.state
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(", "),  # split each genre back to a list
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.searching_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }
    return render_template("forms/edit_venue.html", form=form, venue=data)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)

    if form.validate():
        error = None
        try:
            venue = Venue.query.get(venue_id)
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.phone = form.phone.data
            venue.address = form.address.data
            venue.image_link = form.image_link.data
            venue.facebook_link = form.facebook_link.data
            venue.genres = ", ".join(form.genres.data)
            venue.website_link = form.website_link.data
            venue.searching_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data

            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            flash(
                f"An error occurred. Venue {form.name.data} info could not be updated. Please try again!", 'error')
            abort(500)
        else:
            # on successful db insert, flash success
            flash("Venue " + form.name.data +
                  " info was successfully updated!")
            return redirect(url_for("show_venue", venue_id=venue_id))
    else:
        venue = Venue.query.get(venue_id)
        error_msg = error_msg_constructor(form.errors)
        flash(
            f"Venue, \"{form.name.data}\" info could not be updated. An error occurred ({error_msg})", "error")
        return render_template("forms/edit_venue.html", form=form, venue=venue)


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # called upon submitting the new artist listing form
    form = ArtistForm(request.form)
    if form.validate():
        error = False
        try:
            name = form.name.data
            city = form.city.data
            state = form.state.data
            phone = form.phone.data
            image_link = form.image_link.data
            facebook_link = form.facebook_link.data
            genres = ", ".join(form.genres.data)
            website_link = form.website_link.data
            searching_venue = form.seeking_venue.data
            seeking_description = form.seeking_description.data

            artist = Artist(
                name=name,
                city=city,
                state=state,
                phone=phone,
                image_link=image_link,
                facebook_link=facebook_link,
                genres=genres,
                website_link=website_link,
                searching_venue=searching_venue,
                seeking_description=seeking_description,
            )
            db.session.add(artist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            # on unsuccessful db insert, flash error.
            flash(
                f"An error occurred. Artist, \"{form.name.data}\" could not be listed.", "error")
            abort(500)
        else:
            # on successful db insert, flash success
            flash("Artist, " +
                  request.form["name"] + " was successfully listed!")
            return redirect(url_for("artists"))
            # return render_template('pages/home.html')
    else:
        error_msg = error_msg_constructor(form.errors)
        flash(
            f"Artist, \"{form.name.data}\" could not be listed. An error occurred ({error_msg})", "error")
        return render_template("forms/new_artist.html", form=form)

#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    data = []
    shows = Show.query.all()
    for show in shows:
        artist = Artist.query.get(show.artist_id)
        venue = Venue.query.get(show.venue_id)
        show_data = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time),
        }
        data.append(show_data)
    data.reverse
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    error = None
    try:
        form = ShowForm(request.form)
        artist_id = form.artist_id.data
        venue_id = form.venue_id.data
        # start_time = form.start_time.data
        start_time = request.form.get("start_time", "")
        show = Show(artist_id=artist_id, venue_id=venue_id,
                    start_time=start_time)
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash("An error occurred. Show could not be listed.", 'error')
        abort(500)
    else:
        # on successful db insert, flash success
        flash("Show was successfully listed!")
        return redirect(url_for("shows"))


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0")

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
