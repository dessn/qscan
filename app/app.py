#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__    = 'Danny Goldstein <dgold@berkeley.edu>'
__whatami__   = 'Flask server backend for qscan, a mobile-first web application'\
                'that allows one to quickly scan detections of DES SN candidates.'
__version__   = '0.0.1'
__copyright__ = 'Copyright 2014, Danny Goldstein'

# Database interaction occurs exclusively with a MongoDB at NERSC.  DB
# connection info is stored in the `qscan.config` module, and form
# classes are stored in the `qscan.forms` module. Flask-bootstrap
# keeps the website looking sharp.

import logging
import pymongo 
from qscan import config, forms 
from flask.ext.bootstrap import Bootstrap
from flask import Flask, g, render_template, request, jsonify

# Application Creation + Configuration

app = Flask(__name__, static_url_path = 'static/')
app.debug = True

# Give templates easy access to Twitter bootstrap with
# flask-bootstrap.

bootstrap = Bootstrap(app) 

# Open a MongoDB request before each request. 

@app.before_request
def create_mongoclient():
    g.db = pymongo.MongoClient(config.MONGODB_RW_URI)

# And tear it down afterwards.

@app.teardown_reqeuest
def destroy_mongoclient():
    db = getattr(g, db, None)
    if db is not None:
        db.close()

@app.before_first_request
def configure_logging() :
    """Replace Flask's default logging handler(s)."""
    del app.logger.handlers[ : ]
    handler = logging.StreamHandler()
    handler.setFormatter( logging.Formatter( "%(asctime)-15s %(levelname)-8s %(message)s" ) )
    app.logger.addHandler( handler )
    app.logger.setLevel( logging.DEBUG )

# Number of objects to fetch during AJAX calls and when index is loaded. 
N_FETCH = 10

def fetch():
    
    """Return the format string of N_FETCH unscanned objects.  On the
    backend, initialize them by setting their status to viewed, but
    not saved."""

    object_collection = getattr(g.db, 
                                config.MONGODB_OBJECT_COLLECTION_NAME)
    scan_collection   = getattr(g.db,
                                config.MONGODB_SCAN_COLLECTION_NAME)
    
    # Get objects to scan.
    new_objects = scan_collection.find({'scanned':False})

    # Once objects are loaded, their "scanned" field is set to 0,
    # meaning they were looked at, but not saved.
    for obj in new_objects:
        obj['scanned'] = 0
    scan_collection.update(new_objects)

    # Links to the images of the objects are loaded
    snobjids = [ob['snobjid'] for ob in new_objects]
    link_set = object_collection.find({'snobjid':{'$in':snobjids}}, {'fmtstr':1})
    links = [d['fmtstr'] for d in link_set]
    return links

@app.route("/")
def index():
    links = fetch()
    return render_template("index.html", links=links)

@app.route("/register_scan")
def register_scan():
    
    """This method gets called when somebody touches a frame as they
    scan. It flips the boolean value of the ``scanned'' field of the
    object in the mongoDB scan document collection, then returns a
    json response that is True if the flip was successful, false
    otherwise."""

    snobjid = request.args.get('snobjid', 0, type=int)
    scan_collection = getattr(g.db,
                              config.MONGODB_SCAN_COLLECTION_NAME)

    # Find the object's scan record. 
    obj = scan_collection.find_one({'snobjid':snobjid})

    # If one does not exist, return a negative response.
    if obj is None:
        return jsonify(flip=False)

    # Flip the scan decision. 
    obj['scanned'] = not obj['scanned']

    # Update the database. 
    scan_collection.update(obj)

    # Return success.
    return jsonify(flip=True)

@app.route("/fetch_more")
def ajax_fetch():
    links = fetch()
    return jsonify(links=links)
    
