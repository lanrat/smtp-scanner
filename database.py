import sqlite3 as lite

DEBUG = False


class DomObject:
    def __init__(self, domain):
        domain = domain.lower()
        self.domain = domain
        self.mx = dict()

    def add(self, mxk, perf, serv):
        if not self.mx.has_key(mxk):
            self.mx[mxk] = [perf, []]

        self.mx[mxk][1].append(serv)

class Database:
    """Database for storing SMTP security results"""

    def __init__(self,create=True):
        """Initialize the database"""
        self.con = lite.connect('results.db')
        self.cur = self.con.cursor()

        self.cur.execute('SELECT SQLITE_VERSION()')
        data = self.cur.fetchone()
        if DEBUG:
            print "SQlite version %s" % data

        if create:
            # Create initial tables
            self.cur.execute("CREATE TABLE IF NOT EXISTS Domains(Id INTEGER \
                    PRIMARY KEY AUTOINCREMENT, Domain TXT NOT NULL UNIQUE);")
            self.cur.execute("CREATE TABLE IF NOT EXISTS Mx(Id INTEGER PRIMARY \
                    KEY AUTOINCREMENT, Domain TXT NOT NULL UNIQUE, Priority INT);")
            self.cur.execute("CREATE TABLE IF NOT EXISTS Domain_Mx(Id INTEGER \
                    PRIMARY KEY AUTOINCREMENT, Domain_id INT NOT NULL, Mx_id INT NOT NULL);")
            self.cur.execute("CREATE TABLE IF NOT EXISTS Server(Id INTEGER \
                    PRIMARY KEY AUTOINCREMENT, Mx_id INT NOT NULL, IP TXT NOT NULL, ESMTP BIT, \
                    TLS BIT, SSL_Ciper_Name TXT, SSL_Cipher_Version TXT, \
                    SSL_Cipher_Bits INT, SSL_Verified BIT);")
            self.cur.execute("CREATE TABLE IF NOT EXISTS Mx_Server(Id INTEGER \
                    PRIMARY KEY AUTOINCREMENT, Mx_id INT NOT NULL, Server_id INT NOT NULL);")
            #create indexes
            self.cur.execute("CREATE INDEX IF NOT EXISTS Domains_name_index on Domains (Domain);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS Mx_name_index on Mx (Domain);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS Domains_Mx_domain_index on Domain_Mx (Domain_id);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS Domains_Mx_mx_index on Domain_Mx (Mx_id);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS Mx_server_mx_index on Mx_server (Mx_id);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS Mx_server_domain_index on Mx_server (Server_id);")
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

        if dom.mx is None:
            return 
        dom_id = self.add_domain(dom.domain)
        if dom_id == -1:
            return
        for __x, __y in dom.mx.iteritems():
            mx_id, new = self.add_mx(dom_id, __x, __y[0])
            if new:
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
        domain = domain.lower()
        r = self.cur.execute("SELECT * FROM Domains WHERE Domain = '%s';" \
                % domain).fetchone()
        if r is not None:
            return -1
        self.cur.execute("INSERT INTO Domains(Domain) VALUES ('%s');" \
                % domain)
        return self.cur.lastrowid


    def check_mx_record(self, domain):
        return self.cur.execute("SELECT * FROM Mx WHERE Domain = '%s';" \
                % domain).fetchone()

    def add_mx(self, domain_id, domain, priority):
        """Add MX record
        
        Paramaters:
            domain_id -- id of domain record
            domain -- string of domain name
            priority -- priority of mx record
        Return:
            id of new record
        """
        domain = str(domain).lower()
        # If Mx record doees not exists, add it
        mx = self.check_mx_record(domain)
        new = False
        if mx is not None:
            mx_id = mx[0]
        else:
            new = True
            self.cur.execute("INSERT INTO Mx VALUES" \
                    "(NULL, '%s', %d);" % (domain, priority))
            mx_id = self.cur.lastrowid

        self.cur.execute("INSERT INTO Domain_Mx VALUES (NULL, %d, %d);" \
                % (domain_id, mx_id))

        return mx_id, new

    def check_server_record(self, ip):
        return self.cur.execute("SELECT * FROM Server WHERE ip = '%s';" \
                % serv.ip).fetchone()

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

        new = False
        s = self.check_server_record(serv.ip)
        if serv is not None:
            serv_id = s[0]
        else:
            new = True
            self.cur.execute("INSERT INTO Server VALUES" \
                    "(NULL, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s');" \
                    % (mx_id, serv.ip, serv.esmtp, serv.tls, \
                    serv.ssl_cipher_name, serv.ssl_cipher_version, \
                    serv.ssl_cipher_bits, serv.ssl_verified))
            serv_id = self.cur.lastrowid

        self.cur.execute("INSERT INTO Mx_Server VALUES (NULL, %d, %d);" \
                % (mx_id, serv_id))

        return serv_id
