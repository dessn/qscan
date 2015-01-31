#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__     = ['random_snobs']
__author__  = 'Danny Goldstein <dgold@berkeley.edu>'
__whatami__ = 'Opening database connections and fetching data from '\
              'DESOPER is slow. Because we know exactly what  data '\
              'we need to read, we can transfer what we need to    '\
              "NERSC Mongo so that we don't have to deal with slow "\
              'speeds.'

import config
import pymongo
import logging 
import cx_Oracle
from argparse import ArgumentParser

ML_VERSION = 2

def random_snobs(oracle_dbi, mongodb_object_collection, num):

    """Select `num` random detections of variability from DES SN Y2,
    returning a list of dictionaries that can be converted into JSON
    and shoved into Mongo. To save space, the value mapped to the
    fmtstr key of each dictionary is a format string with a %s field
    that can be replaced with` 'srch', 'temp', or 'diff' to yield the
    public URLs of stamp gifs at NCSA."""
 
    dicts = [] # we will return this
    iters = 0  # this keeps track of the number of times we needed to
               # load more random snobjids

    colnames = ['snobjid', 'expnum', 'nite', 'mjd',
                'field', 'ccdnum', 'band', 'seqnum',
                'reqnum', 'attnum', 'ml_score', 'ml_version']

    # Query below originally from JF, I modify it slightly here.
    
    query = 'select distinct o.SNOBJID, o.EXPNUM, o.NITE, o.MJD, '\
            'o.field, o.ccdnum, o.band, lsub.SEQNUM, lsub.REQNUM, '\
            'lsub.ATTNUM, a.ML_SCORE, a.ML_VERSION from snobs o '\
            'JOIN TASK on o.TASK_ID=TASK.ID '\
            'JOIN LATEST_SNSUBMIT lsub on lsub.TASK_ID=TASK.ROOT_TASK_ID '\
            'JOIN SNAUTOSCAN a on o.snobjid = a.snobjid '\
            'where o.STATUS>=0 AND o.SNOBJID=:objid AND a.ML_VERSION=:mlv'

    oid_query = 'select snobjid from snobs where snfake_id = 0'\
                ' order by dbms_random.value'

    # This method has been structured the way it has for speed.
    # Naively, one would expect a query against the joined tables
    # above (with rows ordered randomly) that fetches the first `num`
    # results to be a better way of doing this than first generating a
    # list of random SNOBJIDs and querying the joined tables with a
    # where clause for each row. But in fact, the latter way is
    # faster.  We do it here.

    # We need the while loop since some of the rows generated randomly
    # by the first query may not have any results in the second query,
    # so we keep fetching num random snobjids until num successful
    # rows have been generated.

    while len(dicts) < num:
        
        iters += 1
        
        logging.debug("Fetching round %d of candidate snobjids..." % iters)
        oracle_dbi.execute(oid_query)

        candidate_oid_qresult = oracle_dbi.fetchmany(num)
        logging.debug("Fetched %d candidate snobjids." \
                      % len(candidate_oid_qresult))

        candidate_oids = [elem for elem, in candidate_oid_qresult]

        for snobjid in candidate_oids:

            # Stop once we have `num` successful rows and return. 
            
            if len(dicts) == num:
                break
            
            logging.debug('Executing %s.' % query.replace(':objid', str(snobjid))\
                                                 .replace(':mlv', str(ML_VERSION)))
            oracle_dbi.execute(query, objid=snobjid, mlv=ML_VERSION)
    
            query_result = oracle_dbi.fetchone()
            logging.debug('Fetched: %s' % str(query_result))

            # If a snobjid is not present in the joined tables, it
            # probably comes from data that were deleted or declared
            # bad. Ignore.
            
            if query_result is None:
                logging.debug('Query for %d returned None, continuing.' % snobjid)
                continue

            # Make the query result into a dictionary, and postprocess
            # values.

            rdict = dict(zip(colnames, query_result))

            # But be careful not to accept any rows that are already present in
            # the MongoDB.

            if mongodb_object_collection.find({'snobjid':rdict['snobjid']}).count() > 0:
                logging.debug('%d is already present in Mongo; continuing.' % snobjid)
                continue

            if rdict['ccdnum'] < 10:
                rdict['ccdnum'] = '0%d' % rdict['ccdnum']
            if rdict['attnum'] < 10:
                rdict['attnum'] = '0%d' % rdict['attnum']
            rdict['type'] = '%s'

            # Use a formula to compute the HTTP address at NCSA of the
            # detection's stamps.

            urlbase     = 'http://dessne.cosmology.illinois.edu/SNWG/stamps/stamps_Y2'
            fmtstr_base = '%s/{nite}-r{reqnum}/D_SN-{field}_{band}_s{seqnum}/p{attnum}'\
                          '/ccd{ccdnum}/stamps/{type}{snobjid}.gif' % urlbase
            fmtstr      = fmtstr_base.format(**rdict)
            logging.debug('Link was: %s' % fmtstr)
            rdict['fmtstr'] = fmtstr
            dicts.append(rdict)
    return dicts

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('numget', help='Number of new detections of variability '\
                                       'to add to the MongoDB.',
                        type=int, default=10000)
    parser.add_argument('--debug', '-d', help='Log debug messages to the console.',
                        action='store_true', dest='debug')
    parser.add_argument('--empty-mongo-objects', '--emo', help='Remove all documents from the MongoDB object'\
                                              'collection at the beginning of execution.',
                        action='store_true', dest='emo')
    parser.add_argument('--empty-mongo-scan', '--ems', help='Remove all documents from the MongoDB scan collection '\
                        'at the beginning of execution.', action='store_true', dest='ems')
    args = parser.parse_args()

    # Configure logging. 
    logging.basicConfig(format='[%(asctime)s %(levelname)s]: %(message)s',
                        level=logging.DEBUG if args.debug else logging.INFO)

    oracle_dbi = cx_Oracle.connect(config.ORACLE_URI).cursor()
    mongo_dbi = getattr(pymongo.MongoClient(config.MONGODB_RW_URI),
                        config.MONGODB_DBNAME)
    mongodb_object_collection = getattr(mongo_dbi, config.MONGODB_OBJECT_COLLECTION_NAME)
    mongodb_scan_collection   = getattr(mongo_dbi, config.MONGODB_SCAN_COLLECTION_NAME)
    
    # Delete everything in the MongoDB object table if `emo` is
    # flagged at the command line.

    if args.emo:
        logging.debug('%s MongoDB collection has %d documents.' % \
                      (config.MONGODB_OBJECT_COLLECTION_NAME,
                       mongodb_object_collection.count()))
        logging.debug('Removing all documents from collection...')
        mongodb_object_collection.remove()
        logging.debug('%s now contains %d documents.' %
                      (config.MONGODB_OBJECT_COLLECTION_NAME,
                       mongodb_object_collection.count()))

    # Delete everything in the MongoDB scan table if `ems` is flagged
    # at the command line.

    if args.ems:
        logging.debug('%s MongoDB collection has %d documents.' % \
                      (config.MONGODB_SCAN_COLLECTION_NAME,
                       mongodb_scan_collection.count()))
        logging.debug('Removing all documents from collection...')
        mongodb_object_collection.remove()
        logging.debug('%s now contains %d documents.' %
                      (config.MONGODB_SCAN_COLLECTION_NAME,
                       mongodb_scan_collection.count()))
        

    # Business logic is the following four lines. 
    dicts = random_snobs(oracle_dbi, mongodb_object_collection, args.numget)
    mongodb_object_collection.insert(dicts)
    mongodb_scan_collection.insert([{'snobjid':d['snobjid'], 'label':None} for d in dicts])
    logging.info('Successfully transferred %d records from NCSA to NERSC.' % len(dicts))
    
