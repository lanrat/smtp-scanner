#/usr/bin/python

import sys
import sqlite3
import re

if len(sys.argv) < 2:
    print "Please specify a file with a list of email details"
    sys.exit()

dbFile = '/scratch/results_top-million.db'
inFile = open(sys.argv[1])

domMatch = re.compile("^[a-z]")

state = 0
domain = None
domList = []
domDict = {}

for line in inFile:
    line = line[:-1]
    line = line.lower()

    try:
        if domMatch.match(line):
            domList.append(line)
            domDict[line] = {'tls' : None}
            domain = line
            state = 1
            #print "DOMAIN: %s" % domain

        elif state == 1:
            tot = line[8:-1]
            domDict[domain]['total'] = int(tot)
            state = 2
            #print "TOTAL: %d" % int(tot)

        elif state == 2:
            frac = line[11:-1]
            domDict[domain]['fraction'] = float(frac)
            state = 0
            #print "FRACTION: %f" % (float(frac) / 100.)

    except:
        print line
        raise

inFile.close()

con = sqlite3.connect(dbFile)

domStr = "','".join(domList)

query = "SELECT Distinct d.Domain, s.TLS, s.SSL_Verified " \
        + "FROM Domains d " \
        + "INNER JOIN Domain_Mx dm ON d.Id=dm.Domain_id " \
        + "INNER JOIN Mx m ON dm.Mx_id=m.Id " \
        + "INNER JOIN Server s ON s.Mx_id=m.Id " \
        + "WHERE lower(d.domain) IN ('%s');" % (domStr)

res = con.execute(query)

goodPct = 0
goodList = []
badPct = 0
badList = []

for rec in res:
    domain = rec[0]
    tls = rec[1]
    verified = rec[2]

    if verified in ('None', 'False'):
        badPct += domDict[domain]['fraction']
        domDict[domain]['tls'] = False
    else:
        goodPct += domDict[domain]['fraction']
        domDict[domain]['tls'] = True

con.close()

print "Good: %.2f%%" % (goodPct)
print "Bad:  %.2f%%" % (badPct)
