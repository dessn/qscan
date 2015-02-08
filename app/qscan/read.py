#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Danny Goldstein <dgold@berkeley.edu>'
__whatami__ = 'Read list of candidate-associated detections into MongoDB.'
__all__ = []

import pymongo
import config
import cx_Oracle
import logging
import numpy as np
from argparse import ArgumentParser
import multiprocessing as mp
from itertools import chain

ml_version = 2
colnames = ['snobjid', 'expnum', 'nite', 'mjd',
            'field', 'ccdnum', 'band', 'seqnum',
            'reqnum', 'attnum', 'ml_score', 'ml_version']

_split = lambda iterable, n: [iterable[:len(iterable)/n]] + \
    _split(iterable[len(iterable)/n:], n - 1) if n != 0 else []

# Query below originally from JF, I modify it slightly here.
query = 'select distinct o.SNOBJID, o.EXPNUM, o.NITE, o.MJD, '\
    'o.field, o.ccdnum, o.band, lsub.SEQNUM, lsub.REQNUM, '\
    'lsub.ATTNUM, a.ML_SCORE, a.ML_VERSION from snobs o '\
    'JOIN TASK on o.TASK_ID=TASK.ID '\
    'JOIN LATEST_SNSUBMIT lsub on lsub.TASK_ID=TASK.ROOT_TASK_ID '\
    'JOIN SNAUTOSCAN a on o.snobjid = a.snobjid '\
    'where o.STATUS>=0 AND o.SNOBJID=:objid AND a.ML_VERSION=:mlv'

if __name__ == '__main__':

    def run(array_slice):

        """Randomly sample SNOBJIDs from the given array_slice. Each
        time a usable SNOBJID is sampled, acquire the mutex_counter
        lock and increment the value. When the termination value on
        the counter is reached, return the aggregated results."""

        oracle_dbi = cx_Oracle.connect(config.ORACLE_URI,
                                       threaded=True).cursor()    
        db = getattr(pymongo.MongoClient(config.MONGODB_RW_URI),
                     config.MONGODB_DBNAME)

        dicts = list() # This will be populated and returned

        for row in array_slice:
            oracle_dbi.execute(query, mlv=ml_version, objid=int(row['SNOBJID']))
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
            rdict['label'] = None

            # Update the mutex_counter.
            with lock:
                if mutex_counter.value == args.numget:
                    break
                else:
                    mutex_counter.value += 1
                    logging.debug('updated mutex_counter: %d' % mutex_counter.value)
            dicts.append(rdict)

        oracle_dbi.close()
        db.connection.close()
        return dicts

    parser = ArgumentParser()
    parser.add_argument('numget', help='Number of new detections of variability '\
                        'to add to the MongoDB.',
                        type=int, default=10000)
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

    db = getattr(pymongo.MongoClient(config.MONGODB_RW_URI),
                                 config.MONGODB_DBNAME)

    collection = getattr(db, config.MONGODB_COLLECTION_NAME)

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

    logging.debug('number of entries in data: %d' % len(data))
    logging.debug('number of unique entries in data: %d' % len(np.unique(data)))

    # Shuffle it.
    np.random.shuffle(data)

    # Initialize the shared counter.
    mutex_counter = mp.RawValue('i', 0)
    
    # Initialize the lock for the shared counter.
    lock = mp.Lock()
    
    # Fork worker processes.
    p = mp.Pool(processes=args.njobs)

    # Partition the data array.
    splseq = _split(data, args.njobs)
            
    # Do business. 
    dicts = list(chain(*p.map(run, splseq)))
    collection.insert(dicts)
    logging.info('Successfully transferred %d records from NCSA to NERSC.' % len(dicts))
    logging.info('But the number of UNIQUE records was %d.' % len(set([d['snobjid'] for d in dicts])))

