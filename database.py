import sqlite3 as lite

DEBUG = False


class DomObject:
    def __init__(self, domain):
        self.domain = domain
        self.mx = dict()

    def add(self, mxk, perf, serv):
        if not self.mx.has_key(mxk):
            self.mx[mxk] = [perf, []]

        self.mx[mxk][1].append(serv)

class Database:
    """Database for storing SMTP security results"""

    def __init__(self):
        """Initialize the database"""
        self.con = lite.connect('data.db')
        self.cur = self.con.cursor()

        self.cur.execute('SELECT SQLITE_VERSION()')
        data = self.cur.fetchone()
        if DEBUG:
            print "SQlite version %s" % data

        # Create initial tables
        self.cur.execute("CREATE TABLE IF NOT EXISTS Domains(Id INTEGER \
                PRIMARY KEY AUTOINCREMENT, Domain TXT);")
        self.cur.execute("CREATE TABLE IF NOT EXISTS Mx(Id INTEGER PRIMARY \
                KEY AUTOINCREMENT, Domain TXT, Priority INT);")
        self.cur.execute("CREATE TABLE IF NOT EXISTS Domain_Mx(Id INTEGER \
                PRIMARY KEY AUTOINCREMENT, Domain_id INT, Mx_id INT);")
        self.cur.execute("CREATE TABLE IF NOT EXISTS Server(Id INTEGER \
                PRIMARY KEY AUTOINCREMENT, Mx_id INT, IP TXT, ESMTP BIT, \
                TLS BIT, SSL_Ciper_Name TXT, SSL_Cipher_Version TXT, \
                SSL_Cipher_Bits INT, SSL_Verified BIT);")
        #create indexes
        self.cur.execute("CREATE INDEX Domains_name_index on Domains (Domain);")
        self.cur.execute("CREATE INDEX Mx_name_index on Mx (Domain);")
        self.cur.execute("CREATE INDEX Domains_Mx_domain_index on Domains_Mx (Domain_id);")
        self.cur.execute("CREATE INDEX Domains_Mx_mx_index on Domains_Mx (Mx_id);")
        #commit changes
        self.con.commit()

    def __del__(self):
        """Cleanup"""
        self.con.commit()
        if self.con: 
            self.con.close()
    
    def add(self, dom):
        """Add record
        
        Paramaters:
            dom -- object containing domain, mx list, and server lists
        """

        dom_id = self.add_domain(dom.domain)
        for __x, __y in dom.mx.iteritems():
            mx_id = self.add_mx(dom_id, __x, __y[0])
            for serv in dom.mx[__x][1]:
                self.add_server(mx_id, serv)
        self.con.commit()

    def add_domain(self, domain):
        """Add domain record
        
        Paramaters:
            domain -- string of domain to add
        Return:
            id of new record
        """

        self.cur.execute("INSERT INTO Domains(Domain) VALUES ('%s');" \
                % domain)
        return self.cur.lastrowid


    def add_mx(self, domain_id, domain, priority):
        """Add MX record
        
        Paramaters:
            domain_id -- id of domain record
            domain -- string of domain name
            priority -- priority of mx record
        Return:
            id of new record
        """

        # If Mx record doees not exists, add it
        r = self.cur.execute("SELECT * FROM Mx WHERE Domain = '%s';" \
                % domain).fetchone()
        if r is not None:
            mx_id = r[0]
        else:
            self.cur.execute("INSERT INTO Mx VALUES" \
                    "(NULL, '%s', %d);" % (domain, priority))
            mx_id = self.cur.lastrowid

        self.cur.execute("INSERT INTO Domain_Mx VALUES (NULL, %d, %d);" \
                % (domain_id, mx_id))

        return mx_id


    def add_server(self, mx_id, serv):
        """Add Server record
        
        Paramaters:
            mx_id -- id of MX record
            serv -- smtp_server object
        Return:
            id of new record
        """

        if serv is None:
            return -1

        self.cur.execute("INSERT INTO Server VALUES" \
                "(NULL, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s');" \
                % (mx_id, serv.ip, serv.esmtp, serv.tls, \
                serv.ssl_cipher_name, serv.ssl_cipher_version, \
                serv.ssl_cipher_bits, serv.ssl_verified))
        return self.cur.lastrowid
