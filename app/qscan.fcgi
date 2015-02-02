#!/usr/bin/env python

from flup.server.fcgi import WSGIServer
from app import app

if __name__ == '__main__':
   WSGIServer(app, bindAddress = ( "0.0.0.0", 5000 ) ).run()
