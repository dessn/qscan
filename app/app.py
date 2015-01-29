#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Danny Goldstein <dgold@berkeley.edu>'
__whatami__ = 'Flask server backend for qscan, a web application that '\
              'allows one to quickly scan detections of DES SN candidates.'
__version__ = '0.0.1'
__copyright__ = 'Copyright 2014, Danny Goldstein'

import logging
import pymongo
import cx_Oracle
import config
from forms import UserForm
from flask import Flask, g, render_template, request

app = Flask(__name__, static_url_path = 'static/')

# set secret key in order to use session
app.secret_key = '\xfdV\xb7\xb2\xacQgf\xa3W\xad\xd3\xdd\x12\xd9 \x0cPR4\x9b\xb1iM'
#Set so we don't need to reload the app every time we make a change
app.debug = True

#Configure login 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = None
login_manager.login_view = "login"


#Define user_loader callback so user information can be obtained from userid
@login_manager.user_loader        
def load_scanner(scanner_id):
    """Query database with user_id, create User object with info from query result
    and return the User object"""
    
    #Cast user_id to int for query
    user_id = int(user_id)
    userresult = User.query.filter(User.id==user_id)
    user = userresult.first()

    #For use in templates
    session['logged_in']=True
    return user

def set_session_key(key, value):
    """Use to set a session key or value"""
    session[key] = value

@app.before_first_request
def configure_logging() :
    """Replace Flask's default logging handler(s)."""
    del app.logger.handlers[ : ]
    handler = logging.StreamHandler()
    handler.setFormatter( logging.Formatter( "%(asctime)-15s %(levelname)-8s %(message)s" ) )
    app.logger.addHandler( handler )
    app.logger.setLevel( logging.DEBUG )

@app.before_request
def db_connection() :
    """Prepare the MongoDB client and database objects.  Any preprocessing that
    requires access to the database must come after this.
    Defines: g.dbi."""
    
    g.dbi = pymongo.MongoClient(config.MONGODB_RW_URI)
    g.oracle_dbi = cx_Oracle.connect(config.ORACLE_URI, threaded=True).cursor()

@app.route("/")
def index():
    login_form 
    return render_template("login.html", form=)

def gifurl_fmtstr(snobjid):
    """Generate a format string with a %s field that can be replaced with
    the 'srch', 'temp', or 'diff' to yield the URL of stamp gifs at 
    NCSA.

    FIXME: Currently only works for Y2.
    """
    
    # Query below from JF.

    colnames = ['snobjid', 'expnum', 'nite', 'mjd',
                'field', 'ccdnum', 'band', 'seqnum',
                'reqnum', 'attnum']
    
    query = 'select distinct o.SNOBJID, o.EXPNUM, o.NITE, o.MJD, '\
            'o.field, o.ccdnum, o.band, lsub.SEQNUM, lsub.REQNUM, '\
            'lsub.ATTNUM from snobs o JOIN TASK on o.TASK_ID=TASK.ID '\
            'JOIN LATEST_SNSUBMIT lsub on lsub.TASK_ID=TASK.ROOT_TASK_ID '\
            'where o.STATUS>=0 and o.SNOBJID = :objid'

    g.oracle_dbi.execute(query, objid=snobjid)
    rdict = dict(zip(colnames, g.oracle_dbi.fetchone()))

    if rdict['ccdnum'] < 10:
        rdict['ccdnum'] = '0%d' % rdict['ccdnum']

    urlbase     = 'http://dessne.cosmology.illinois.edu/SNWG/stamps/stamps_Y2'
    fmtstr_base = '%s/{nite}-r{reqnum}/D_SN-{field}_{band}_s{seqnum}/p{attnum}'\
                  '/ccd{ccdnum}/stamps/{type}{snobjid}.fits' % urlbase
    fmtstr      = fmtstr_base.format(**dict(zip(colnames, result)))    
    return fmtstr

@login_required
@app.route("/scan")
def scan():
    user, g.dbi

    # get unscanned stuff

    
