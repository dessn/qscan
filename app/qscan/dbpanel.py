#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = 'Danny Goldstein <dgold@berkeley.edu>'
__whatami__ = 'Summarize qscan MongoDB resources, and provide'\
              'a method to reset all scanning decisions to   '\
              'unviewed.'

import config
import pymongo
import logging
from argparse import ArgumentParser

def summarize_object(oc):
    logging.info('*%s*' % config.MONGODB_OBJECT_COLLECTION_NAME)
    logging.info('%s currently has %d documents.' \
                 % (config.MONGODB_OBJECT_COLLECTION_NAME,
                    oc.count()))
    
def summarize_scan(sc):
    logging.info('*%s*' % config.MONGODB_SCAN_COLLECTION_NAME)
    logging.info('%s currently has %d documents.' \
                 % (config.MONGODB_SCAN_COLLECTION_NAME,
                    sc.count()))
    logging.info('%d of them are currently unviewed (label=None).'\
                 % sc.find({'label':None}).count())
    logging.info('%d of them are currently labelled junk (label=0).'\
                 % sc.find({'label':0}).count())
    logging.info('%d of them are currently saved (label=1).'\
                 % sc.find({'label':1}).count())

def reset_scan(sc):
    logging.info("Resetting 'label' fields of all %s documents to `unviewed`..." \
                 % config.MONGODB_SCAN_COLLECTION_NAME)
    sc.update({}, {'$set':{'label':None}})
    logging.info('%d rows affected.' % \
                 db.run_command({'getLastError':1})['n'])

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--debug', '-d', required=False, action='store_true',
                        help='Verbose mode.', dest='debug')
    parser.add_argument('--reset-scan', action='store_true',
                        help='Set the label field of all documents in the '\
                             'MongoDB scan collection to `unviewed`.',
                        dest='rs')
                        
    args = parser.parse_args()
    
    # Setup the logger:

    logging.basicConfig(format="[%(asctime)s %(levelname)s]: %(message)s",
                        level=logging.DEBUG if args.debug else logging.INFO)

    # The following lines open up a connection to the MongoDB, bind
    # each of its collections to python objects, and compute summary
    # statistics for each one. The summary statistics are logged to
    # the logging.INFO level.

    logging.debug('Opening a connection to the MongoDB...')
    db = getattr(pymongo.MongoClient(config.MONGODB_RW_URI),
                 config.MONGODB_DBNAME)
    logging.debug('Connection successful.')

    # Object collection

    logging.debug('Binding the object collection...')
    oc = getattr(db,
                 config.MONGODB_OBJECT_COLLECTION_NAME)
    logging.debug('Object collection bound.')
    
    # Scan collection

    logging.debug('Binding the scanning collection...')
    sc = getattr(db,
                 config.MONGODB_SCAN_COLLECTION_NAME)
    logging.debug('Scanning collection bound.')

    # Summarize object collection:

    summarize_object(oc)
    
    # Summarize scan collection:

    summarize_scan(sc)

    # Reset scanning decisions
    
    if args.rs:
        reset_scan(sc)
        summarize_scan(sc)
        
