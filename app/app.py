#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__    = 'Danny Goldstein <dgold@berkeley.edu>'
__whatami__   = 'Flask server backend for qscan, a mobile-first web application'\
                'that allows one to quickly scan detections of DES SN candidates.'
__version__   = '0.0.1'
__copyright__ = 'Copyright 2014, Danny Goldstein'

# Import Statements

# Database interaction occurs exclusively with a MongoDB at NERSC.  DB
# connection info is stored in the `qscan.config` module, and form
# classes are stored in the `qscan.forms` module. Flask-bootstrap
# keeps the website looking sharp.

import logging
import pymongo 
from qscan import config, forms 
from flask.ext.bootstrap import Bootstrap
from flask import Flask, g, render_template, request

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

@app.route("/")
def index():
    object_collection = getattr(g.db, 
                                config.MONGODB_OBJECT_COLLECTION_NAME)
    scan_collection   = getattr(g.db,
                                config.MONGODB_SCAN_COLLECTION_NAME)
    
    # Get 100 objects to scan.
    
    
    return render_template("login.html", form=)
    
