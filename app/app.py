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

# And tear it down afterwards.

@app.teardown_request
def destroy_mongoclient(exception):
    db = getattr(g, 'db', None)
    dbcon = getattr(g, 'dbcon', None)
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

def fetch(n_fetch=24):
    
    """Return the format string of N_FETCH unviewed objects.  On the
    backend, initialize them by setting their status to viewed, but
    not saved.
    
    Parameters:
    -----------
    n_fetch: int, default=10. 
        Number of objects to fetch.
    """

    object_collection = getattr(g.db, 
                                config.MONGODB_OBJECT_COLLECTION_NAME)
    scan_collection   = getattr(g.db,
                                config.MONGODB_SCAN_COLLECTION_NAME)

    # Get objects to scan.

    app.logger.debug('Fetching %d unscanned objects.' % n_fetch)
    new_objects = scan_collection.find({'label':None}).limit(n_fetch)
    
    # Links to the images of the objects are loaded
    snobjids = [ob['snobjid'] for ob in new_objects]
    app.logger.info('Fetched snobjids: %s.' % snobjids)

    link_set = object_collection.find({'snobjid':{'$in':snobjids}}, 
                                      {'snobjid': 1,'fmtstr':1})
    links = list(link_set)
    return links

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/set_object_label", methods=["POST"])
def set_object_label():
    
    """This method sets the label of a scan object in the MongoDB. It
    gets called when someone looks at an object for the first time and
    when someone clicks on an object."""

    snobjid = int(request.form.get('snobjid'))
    action_type = request.form.get('action') # look, click

    app.logger.debug('set_object_label triggered for SNOBJID %d!' % snobjid)
    scan_collection = getattr(g.db,
                              config.MONGODB_SCAN_COLLECTION_NAME)

    if action_type == 'look':
        scan_collection.update({'snobjid':snobjid}, {'$set':{'label':'Bogus'}})
        
    elif action_type == 'click':
        current_label = scan_collection.find_one({'snobjid':snobjid})['label']
        scan_collection.update({'snobjid':snobjid}, 
                               {'$set':{'label':'Real' if 
                                        current_label == 'Bogus' else 'Bogus'}})
    app.logger.debug('Updated database with %s, %d rows affected.' % (action_type, 
                                                                      g.db.command('getLastError')['n']))
    return jsonify(success=True)

@app.route("/fetch_more")
def ajax_fetch():
    """Query the database backend for unviewed scan-objects. Return JSON
    with two fields: html and has_data. `html` is the formatted HTML to
    append to the DOM of the app's index page. has_data indicates whether
    or not the html contains any new objects, or if it is just a panel 
    that indicates whether objects were found."""
    
    app.logger.debug('Entering ajax_fetch!')
    scan_collection = getattr(g.db,
                              config.MONGODB_SCAN_COLLECTION_NAME)
    has_data = (scan_collection.find({'label':None}).count() > 0)
    links = fetch()
    html = render_template("content.html", links=links)
    response = jsonify(has_data=has_data,
                       html=html,
                       numnew=len(links))
    app.logger.debug('ajax_fetch returning: %s' % response.data)
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=25981)
