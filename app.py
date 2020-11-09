#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask_migrate import Migrate
from flask import (
  Flask,
  render_template,
  request, Response,
  flash, redirect,
  url_for,
  abort,
  jsonify
)
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
import os
from forms import *
import sys
from models import *
from datetime import datetime
#----------------------------------------------------------------------------#
#----------------------------------------------------------------------------#

migrate = Migrate(app, db)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  locs = db.session.query(Venue.city, Venue.state).group_by(Venue.state).group_by(Venue.city).all()
  data=[]
  for loc in locs:
    record = {
    "city": loc.city,
    "state": loc.state,
    "venues": Venue.query.filter_by(city=loc.city).filter_by(state=loc.state).all()}
    data.append(record)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_str = request.form.get('search_term')
  venue_query = Venue.query.filter(Venue.name.ilike('%' + search_str + '%')).all()

  response={
    "count": len(venue_query),
    "data": venue_query
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  venue = Venue.query.get(venue_id)
  upcoming_show = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>current_time).all()
  past_show = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<current_time).all()

  upcoming_shows=[]
  past_shows=[]
  for show in upcoming_show:
    upcoming_shows.append({
      'artist_id': show.artist_id,
      'artist_name': Artist.query.get(show.artist_id).name,
      'artist_image_link': Artist.query.get(show.artist_id).image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for show in past_show:
    past_shows.append({
      'artist_id': show.artist_id,
      'artist_name': Artist.query.get(show.artist_id).name,
      'artist_image_link': Artist.query.get(show.artist_id).image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  data = {
    'name': venue.name,
    'id': venue.id,
    'city': venue.city,
    'state': venue.state,
    'address': venue.address,
    'phone': venue.phone,
    'website': venue.website,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error= False
  body = {}
  try:
    name = request.form['name']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    genre = request.form.getlist('genres')
    phone = request.form['phone']
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    seeking_talent = request.form['seeking_talent']
    print(seeking_talent)
    if seeking_talent == 'Yes':
      seeking_talent = True
    else:
      seeking_talent = False
    seeking_description = request.form['seeking_description']

    venue = Venue(name=name, address=address, city=city, state=state, genres=genre,
                  phone=phone, facebook_link=facebook_link, seeking_talent=seeking_talent,
                  image_link=image_link, website=website,
                  seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Venue ' + name + ' could not be listed.')
    print(sys.exc_info())

  finally:
    db.session.close()

  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    abort(500)

  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    print(venue.name)

    for show in venue.show_list:
      db.session.delete(show)

    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_str = request.form.get('search_term')
  artist_query = Artist.query.filter(Artist.name.ilike('%' + search_str + '%')).all()

  response={
    "count": len(artist_query),
    "data": artist_query
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=Artist.query.get(artist_id))

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist_info = Artist.query.get(artist_id)
  artist={
    "id": artist_id,
    "name": artist_info.name,
    "genres": artist_info.genres,
    "city": artist_info.city,
    "state": artist_info.state,
    "phone": artist_info.phone,
    "website": artist_info.website,
    "facebook_link": artist_info.facebook_link,
    "seeking_venue": artist_info.seeking_venue,
    "seeking_description": artist_info.seeking_description,
    "image_link": artist_info.image_link
  }

  form.genres.data = artist_info.genres
  form.state.data = artist_info.state

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.genres = request.form.getlist('genres')
    print(request.form.getlist('genres'))
    artist.phone = request.form['phone']
    print(request.form['phone'])
    artist.facebook_link = request.form['facebook_link']
    print(request.form['facebook_link'])
    artist.website = request.form['website']
    print(request.form['website'])
    print(request.form['seeking_venue'])
    if request.form['seeking_venue'] == 'Yes':
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False

    artist.seeking_description = request.form['seeking_description']
    artist.image_link = request.form['image_link']
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')
    print(sys.exc_info())

  finally:
    db.session.close()

  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully edited!')
  else:
    abort(500)

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/artists/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  try:
    artist = Artist.query.get(artist_id)

    for show in artist.show_list:
      db.session.delete(show)

    db.session.delete(artist)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return None

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_info = Venue.query.get(venue_id)
  venue={
    "id": venue_id,
    "name": venue_info.name,
    "genres": venue_info.genres,
    "address": venue_info.address,
    "city": venue_info.city,
    "state": venue_info.state,
    "phone": venue_info.phone,
    "website": venue_info.website,
    "facebook_link": venue_info.facebook_link,
    "seeking_talent": venue_info.seeking_talent,
    "seeking_description": venue_info.seeking_description,
    "image_link": venue_info.image_link
  }
  form.genres.data = venue_info.genres
  form.state.data = venue_info.state

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.genres = request.form.getlist('genres')
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    if request.form['seeking_talent'] == 'Yes':
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False
    venue.seeking_description = request.form['seeking_description']
    venue.image_link = request.form['image_link']
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
    print(sys.exc_info())

  finally:
    db.session.close()

  if not error:
    flash('Venue was ' + request.form['name'] + ' successfully edited!')
  else:
    abort(500)
  print('works here')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    genre = request.form.getlist('genres')
    phone = request.form['phone']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    if request.form['seeking_venue'] == 'Yes':
      seeking_venue=True
    else:
      seeking_venue=False
    seeking_description = request.form['seeking_description']
    image_link = request.form['image_link']
    artist = Artist(name=name, city=city, state=state, genres=genre,
                    phone=phone, facebook_link=facebook_link, website=website,
                    seeking_venue=seeking_venue, seeking_description=seeking_description,
                    image_link=image_link)
    db.session.add(artist)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Artist ' + name + ' could not be listed.')
    print(sys.exc_info())

  finally:
    db.session.close()

  if not error:
    flash('Artist ' + name + ' was successfully listed!')
  else:
    abort(500)

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  show_query=Show.query.all()

  data=[]
  for show in show_query:
    data.append({
    "venue_id": show.venue_id,
    "venue_name": Venue.query.get(show.venue_id).name,
    "artist_id": show.artist_id,
    "artist_name": Artist.query.get(show.artist_id).name,
    "artist_image_link": Artist.query.get(show.artist_id).image_link,
    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
    print(sys.exc_info())

  finally:
    db.session.close()

  if not error:
    flash('Show was successfully listed!')
  else:
    abort(500)

  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500



if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

