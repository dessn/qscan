#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Danny Goldstein <dgold@berkeley.edu>'
__whatami__ = 'Creates the list of detections from which '\
              'scannable objects can be drawn.'

from textwrap import dedent
from math import pi
import config
import cx_Oracle
from argparse import ArgumentParser

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('outname', help='Name of ASCII file for result dump.',
                        type=str)
    args = parser.parse_args()

    colnames = ['SNOBJID', 'SNID', 'NUMEPOCHS', 'NUMEPOCHS_ML']
    tol = 1. / 3600. # 1 arcsecond in degrees

    oracle_dbi = cx_Oracle.connect(config.ORACLE_URI).cursor()
    query = dedent("""select o.snobjid, c.snid, c.numepochs, 
                      c.numepochs_ml from sny1reproc.snobs o
                      join sny1reproc.sncand c on o.ra between (c.ra -
                      (:tol / COS(c.dec * :pi / 180.)))
                      and (c.ra + (:tol / COS(c.dec *
                      :pi / 180.))) and o.dec between (c.dec -
                      :tol) and (c.dec + :tol) where
                      c.snfake_id = 0 and c.numepochs >= 2 and c.cand_type >= 0 and
                      o.snfake_id = 0""")

    oracle_dbi.execute(query, tol=tol, pi=pi)
    result = oracle_dbi.fetchall()
    
    with open(args.outname, 'w') as f:
        f.write('%s\n' % '\t'.join(colnames))
        for row in result:
            f.write('%d\t%d\t%d\t%d\n' % row)
