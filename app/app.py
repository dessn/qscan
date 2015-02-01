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

def fetch(n_fetch=10):
    
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

    # Once objects are loaded, initialize their "label" field to 0.
    # This means they were looked at, but not saved.
    scan_collection.update({'snobjid':{'$in':snobjids}},
                           {'$set':{'label':0}},
                           multi=True)

    link_set = object_collection.find({'snobjid':{'$in':snobjids}}, 
                                      {'snobjid': 1,'fmtstr':1})
    links = list(link_set)
    return links

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register_scan", methods=["POST"])
def register_scan():
    
    """This method gets called when somebody touches a frame as they
    scan. It flips the boolean value of the ``label'' field of the
    object in the mongoDB scan document collection, then returns a
    json response that is True if the flip was successful, false
    otherwise."""

    app.logger.debug('register_scan triggered!')
    snobjid = int(request.form.get('snobjid', 0))
    
    app.logger.debug('HTTP request payload contained SNOBJID %d.' % snobjid)
    
    scan_collection = getattr(g.db,
                              config.MONGODB_SCAN_COLLECTION_NAME)

    # Find the object's scan record. 
    obj = scan_collection.find_one({'snobjid':snobjid})

    # If one does not exist, return a negative response.
    if obj is None:
        negative_json_response = jsonify(flip=False)
        app.logger.debug('Object not found in %s. Returning negative '\
                         'JSON response: %s.' % \
                         (config.MONGODB_SCAN_COLLECTION_NAME,
                         negative_json_response))
        return negative_json_response

    app.logger.debug('Object %d was found in %s.' % \
                     (snobjid, config.MONGODB_SCAN_COLLECTION_NAME))

    app.logger.debug('Updating %s with new scan decision.'\
                     '%d is now %d.' % (config.MONGODB_SCAN_COLLECTION_NAME,
                                        snobjid, int(not obj['label'])))

    # Update the database. 
    scan_collection.update({'snobjid':obj['snobjid']},
                           {'$set':{'label':int(not obj['label'])}})
    app.logger.debug('Database updated: %d rows affected.' % \
                     g.db.command('getLastError')['n'])

    # Return success.
    json_success = jsonify(flip=True)
    app.logger.debug('JSON success response: %s.' % json_success)
    return json_success

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
                       html=html)
    app.logger.debug('ajax_fetch returning: %s' % response.data)
    return response

@app.route("/anything_left")
def anything_left():
    """See if there is anything left to scan."""

    app.logger.debug('Anything left called!')
    response = jsonify(answer=answer)
    
    app.logger.debug('Returning response: %s.' % response)
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=25981)
