import logging
import pymongo
import cx_Oracle
import config
from forms import UserForm
from flask import Flask, g, render_template, request

app = Flask(__name__, static_url_path = 'static/')

#set secret key in order to use session
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


def generate_links(snobjid, season):
    """Return a dictionary containing links to the gifs of an
    snobjid."""
    
    cursor = y2prod()

    # following query from john fischer
    # i modify it here slightly

    query = 'select distinct o.SNOBJID, o.EXPNUM, o.NITE, o.MJD, '\
            'o.field, o.ccdnum, o.band, lsub.SEQNUM, lsub.REQNUM, '\
            'lsub.ATTNUM from snobs o JOIN TASK on o.TASK_ID=TASK.ID '\
            'JOIN LATEST_SNSUBMIT lsub on lsub.TASK_ID=TASK.ROOT_TASK_ID '\
            'where o.STATUS>=0 and o.SNOBJID = :objid'
    
    path_list = list()
    
    for snobjid in snobjid_list:
        cursor.execute(query, objid=int(snobjid))
        names = zip(*cursor.description)[0]
        result = np.squeeze(np.array(cursor.fetchall(),
                                     dtype={'names':[name.lower() for name in names],
                                            'formats':convert(cursor.description)}))
        if result.shape != ():
            raise Exception, 'Multiple stamp paths found for %d:\n\t%s' % (snobjid, result)
        
        base = '{preprefix}/{nite}-r{reqnum}/D_SN-{field}_{band}_s{seqnum}/p{attnum}'\
                                                                                                                          '/ccd{ccdnum}/stamps/{type}{snobjid}.fits'
                                                                                                            triplet = list()
                                                                                                            for type in ['srch','temp','diff']:
                                                                                                                            kwargs = dict()
                                                                                                                            for name in result.dtype.names:
                                                                                                                                                kwargs[name] = result[name]
                                                                                                                                                            kwargs['type'] = type
                                                                                                                                                            if kwargs['ccdnum'] < 10:
                                                                                                                                                                                kwargs['ccdnum'] = '0%d' % kwargs['ccdnum']
                                                                                                                                                                                if kwargs['attnum'] < 10:
                                                                                                                                                                                                    kwargs['attnum'] = '0%d' % kwargs['attnum']
                                                                                                                                                                                                                kwargs['preprefix'] = '/home2/SNWG/stamps/stamps_Y2' if local else \
                                                                                                                                                                                                                                                                        'http://dessne.cosmology.illinois.edu/SNWG/stamps/stamps_Y2'
                                                                                                                                                                                                                            triplet.append(base.format(**kwargs))
                                                                                                                                                                                                                                    path_list.append(triplet)

                                                                                                                                                                                                                                                cursor.close()
                                                                                                                                                                                                                                                    return path_list
                                                                                                                                                                                                                                                
    

@login_required
@app.route("/scan")
def scan():
    user, g.dbi

    # get unscanned stuff
