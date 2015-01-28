import logging
import pymongo
from flask import Flask, g, render_template, request

app = Flask(__name__)

@app.before_first_request
def configure_logging() :
    """Replace Flask's default logging handler(s)."""
    del app.logger.handlers[ : ]
    handler = logging.StreamHandler()
    handler.setFormatter( logging.Formatter( "%(asctime)-15s %(levelname)-8s %(message)s" ) )
    app.logger.addHandler( handler )
    app.logger.setLevel( logging.DEBUG )

@app.before_request
def mongodb_connection() :
    """Prepare the MongoDB client and database objects.  Any preprocessing that
    requires access to the database must come after this.
    Defines: g.dbi."""
    
    g.dbi = DBI()
