import sqlite3 as lite
import sys
import re

def sanitize(host):
    host = host.replace("'", "")

    return host

def createTables(con):
    cur = con.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS Domains(Id INTEGER \
            PRIMARY KEY AUTOINCREMENT, Domain TXT NOT NULL UNIQUE);")

    cur.execute("CREATE TABLE IF NOT EXISTS Leaks(Id INTEGER \
            PRIMARY KEY AUTOINCREMENT, Source TXT NOT NULL UNIQUE);")

    cur.execute("CREATE TABLE IF NOT EXISTS Counts(Id INTEGER PRIMARY \
            KEY AUTOINCREMENT, Domain_id INT NOT NULL, Leak_id INT NOT NULL, \
            Count INT);")

    cur.execute("CREATE INDEX IF NOT EXISTS Domains_name_index on Domains (Domain);")
    cur.execute("CREATE INDEX IF NOT EXISTS Counts_domain_index on Counts (Domain_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS Counts_leak_index on Counts (Leak_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS Counts_count_index on Counts (Count);")

    con.commit()

def getConnection():
    con = lite.connect('email_counts.db')
    return con

def addDomain(con, domain):
    domain = domain.lower()
    cur = con.cursor()
    query = "INSERT INTO Domains (Domain) VALUES ('%s')" % domain
    try:
        cur.execute(query)
        con.commit()
        return cur.lastrowid
    except lite.IntegrityError:
        query = "SELECT Id FROM Domains WHERE Domain='%s'" % domain
        res = cur.execute(query)
        for row in res:
            return row[0]

def addLeakSource(con, source):
    source = source.lower()
    cur = con.cursor()
    query = "INSERT INTO Leaks (Source) VALUES ('%s')" % source
    try:
        cur.execute(query)
        con.commit()
        return cur.lastrowid
    except lite.IntegrityError:
        query = "SELECT Id FROM Leaks WHERE Source='%s'" % source
        res = cur.execute(query)
        for row in res:
            return row[0]

def addRecord(con, domain, count, sourceID):
    cur = con.cursor()
    domID = addDomain(con, domain)
    query = "UPDATE Counts SET Count=%d WHERE Domain_id=%d AND Leak_id=%d" \
                    % (count, domID, sourceID)
    print "%s: %s" % (domain, query)
    cur.execute(query)
    if cur.rowcount == 0:
        query = "INSERT INTO Counts (Domain_id, Leak_id, Count) " \
                + "VALUES (%d, %d, %d)" % (domID, sourceID, count)
        cur.execute(query)
    con.commit()
    

def getAdobeEmailCounts(inFile):
    inFile = open(inFile)
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

                domain = sanitize(line)
                if domain != line:
                    print "|%s| => |%s|" % (line, domain)
                if domDict.get(domain):
                    pass
                else:
                    domList.append(domain)
                    domDict[domain] = {'tls' : None, 'total' : 0, 'fraction' : 0.0}
                state = 1
                #print "DOMAIN: %s" % domain

            elif state == 1:
                tot = line[8:]
                try:
                    domDict[domain]['total'] += int(tot)
                except:
                    print "_%s_" % domain
                    raise
                state = 2
                #print "TOTAL: %d" % int(tot)

            elif state == 2:
                frac = line[11:-1]
                domDict[domain]['fraction'] += float(frac)
                state = 0
                #print "FRACTION: %f" % (float(frac) / 100.)

        except:
            print line
            raise

    inFile.close()
    return (domList, domDict)



if len(sys.argv) < 2:
    print "Please specify a file to read in"
    sys.exit(1)

leak = "adobe"

con = getConnection()
createTables(con)

sourceID = addLeakSource(con, leak)
(domains, counts) = getAdobeEmailCounts(sys.argv[1])
for domain in domains:
    c = counts[domain]['total']
    addRecord(con, domain, c, sourceID)

con.close()
