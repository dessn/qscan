#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__    = 'Danny Goldstein <dgold@berkeley.edu>'
__whatami__   = 'Flask server backend for qscan, a mobile-first web application'\
                'that allows one to quickly scan detections of DES SN candidates.'
__version__   = '0.0.1'

# Database interaction occurs exclusively with a MongoDB at NERSC.  DB
# connection info is stored in qscan.config. Flask-bootstrap keeps the
# website looking sharp.

import logging
import pymongo 
from qscan import config 
from flask.ext.bootstrap import Bootstrap
from flask import Flask, g, render_template, request, jsonify

# Application Creation + Configuration

app = Flask(__name__, static_url_path = '/static')
app.debug = True

# Give templates easy access to Twitter bootstrap with
# flask-bootstrap.

bootstrap = Bootstrap(app) 

# Open a MongoDB connection before each request. 

@app.before_request
def create_mongoclient():
    g.dbcon = pymongo.MongoClient(config.MONGODB_RW_URI)
    g.db = getattr(g.dbcon, config.MONGODB_DBNAME)
    g.c = getattr(g.db, config.MONGODB_COLLECTION_NAME)
                   
# And tear it down afterwards.

@app.teardown_request
def destroy_mongoclient(exception):
    db = getattr(g, 'db', None)
    dbcon = getattr(g, 'dbcon', None)
    if g.c is not None:
        del g.c
    if db is not None:
        del db
    if dbcon is not None:
        dbcon.disconnect()

@app.before_first_request
def configure_logging() :
    """Replace Flask's default logging handler(s)."""
    del app.logger.handlers[:]
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s %(levelname)s]: %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)

def fetch(exclude=None, n_fetch=24):
    
    """Return the format string of N_FETCH unviewed objects.  On the
    backend, initialize them by setting their status to viewed, but
    not saved.
    
    Parameters:
    -----------
    exclude: iterable
        Snobjids NOT to return.
    
    n_fetch: int, default=24. 
        Number of objects to fetch.
    """

    # Get objects to scan.

    app.logger.debug('Fetching %d unscanned objects.' % n_fetch)
    new_objects = g.c.find({'label':None,
                            'snobjid':{'$nin':exclude}}).limit(n_fetch)
    
    # Links to the images of the objects are loaded
    snobjids = [ob['snobjid'] for ob in new_objects]
    app.logger.info('Fetched snobjids: %s.' % snobjids)

    link_set = g.c.find({'snobjid':{'$in':snobjids}}, 
                        {'snobjid': 1,'fmtstr':1})
    links = list(link_set)
    return links

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    
    """This method sets the label of a scan object in the MongoDB. It
    gets called when someone looks at an object for the first time and
    when someone clicks on an object."""

    save = map(int, request.form.getlist('save[]'))
    junk = map(int, request.form.getlist('junk[]'))

    app.logger.debug('submitted JUNK snobjids: %s' % junk)
    app.logger.debug('submitted SAVE snobjids: %s' % save)


    g.c.update({'snobjid':{'$in':save}, {'$set':{'label':'Real'}}},
               multi=True)
    app.logger.debug('Updated database, %d rows affected.' % g.db.command('getLastError')['n'])
        
    g.c.update({'snobjid':{'$in':junk}, {'$set':{'label':'Bogus'}}},
               multi=True)
    app.logger.debug('Updated database, %d rows affected.' % g.db.command('getLastError')['n'])
    
    return jsonify(success=True)

@app.route("/fetch_more", methods=["POST"])
def ajax_fetch():
    """Query the database backend for unviewed scan-objects. Return JSON
    with two fields: html and has_data. `html` is the formatted HTML to
    append to the DOM of the app's index page. has_data indicates whether
    or not the html contains any new objects, or if it is just a panel 
    that indicates whether objects were found."""

    exlude = map(int, request.form.getlist('exclude[]'))
    
    app.logger.debug('Entering ajax_fetch!')

    has_data = (g.c.find({'label':None}).count() > 0)
    links = fetch(exclude=exclude)
    html = render_template("content.html", links=links)
    response = jsonify(has_data=has_data,
                       html=html,
                       numnew=len(links))
    app.logger.debug('ajax_fetch returning: %s' % response.data)
    return response

@app.route("/render_done", methods=["POST"])
def done():
    
    """View function for the ``done'' page displaying scanning session
    statistics."""

    app.logger.debug('scanning session complete.')
    numsaved = int(request.form['numsaved'])
    numignored = int(request.form['numignored'])
    numobs = numsaved + numignored
    return render_template('done.html', 
                           numsaved=numsaved,
                           numignored=numignored,
                           numobs=numobs)
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=25981)
