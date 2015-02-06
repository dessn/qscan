#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Danny Goldstein <dgold@berkeley.edu>'
__whatami__ = 'Read list of scannable detections into MongoDB.'

import pymongo
import config
import cx_Oracle
import logging
import numpy as np
from argparse import ArgumentParser
from multiprocessing import Pool

# Split arbitrary sequence `seq` into n roughly even subsequences.
split = lambda seq, n: [seq[:len(seq)/n]] + split(seq[len(seq)/n:], n - 1) \
    if n > 0 else []

ml_version = 2
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


def run_query(data_rows):
    
    """Execute `query` for each row in data_rows.  Insert the results
    into the MongoDB collection.

    Parameters:
    -----------
    
    data_rows: recarray,
       Record array containing SNOBJID, SNID, NUMEPOCHS, NUMEPOCHSML.
    """
    
    oracle_dbi = cx_Oracle.connect(config.ORACLE_URI,
                                   threaded=True).cursor()    
    db = getattr(pymongo.MongoClient(config.MONGODB_RW_URI),
                 config.MONGODB_DBNAME)
    collection = getattr(db, config.MONGODB_COLLECTION_NAME)
    dicts = list()

    for row in data_rows:
        oracle_dbi.execute(query, mlv=ml_version, snobjid=int(row['SNOBJID']))
                    query_result = oracle_dbi.fetchone()

        # If a snobjid is not present in the joined tables, it
        # probably comes from data that were deleted or declared
        # bad. Ignore.

        if query_result is None:
            continue

        # Make the query result into a dictionary, and postprocess
        # values.

        rdict = dict(zip(colnames, query_result))

        # But be careful not to accept any rows that are already present in
        # the MongoDB.

        if collection.find({'snobjid':rdict['snobjid']}).count() > 0:
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
        rdict['snid'] = row['SNID']
        rdict['numepochs'] = row['NUMEPOCHS']
        rdict['numepochs_ml'] = row['NUMEPOCHS_ML']
        dicts.append(rdict)
    collection.insert(dicts)
    oracle_dbi.close()
    db.close()

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('infile', help='Name of the ASCII file to read.',
                        type=str)
    parser.add_argument('--n_jobs', help='Number of processes to spawn.',
                        type=int, default=1, dest='njobs')
    parser.add_argument('--debug', '-d', help='Log debug messages to the console.',
                        action='store_true', dest='debug')
    parser.add_argument('--empty-mongo-objects', '--emo', help='Remove all documents from the MongoDB object'\
                                              'collection at the beginning of execution.',
                        action='store_true', dest='emo')
    args = parser.parse_args()

    # Configure logging. 
    logging.basicConfig(format='[%(asctime)s %(levelname)s]: %(message)s',
                        level=logging.DEBUG if args.debug else logging.INFO)

    # Delete everything in the MongoDB object table if `emo` is
    # flagged at the command line.

    collection = getattr(getattr(pymongo.MongoClient(config.MONGODB_RW_URI),
                                 config.MONGODB_DBNAME),
                         config.MONGODB_COLLECTION_NAME)

    if args.emo:
        logging.debug('%s MongoDB collection has %d documents.' % \
                      (config.MONGODB_COLLECTION_NAME,
                       collection.count()))
        logging.debug('Removing all documents from collection...')
        collection.remove()
        logging.debug('%s now contains %d documents.' %
                      (config.MONGODB_COLLECTION_NAME,
                       collection.count()))

    # Read in data from ASCII file. 
    data = np.genfromtxt(args.infile,
                         names=True,
                         dtype=None)

    # Execute DB queries in parallel. 
    p = Pool(n_jobs)
    splseq = split(data, args.njobs)
    blocked = p.map_async(run_query, splseq)
    result = blocked.get()
    
