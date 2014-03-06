import sqlite3 as lite

DEBUG = False


class domObject:
    def __init__(self, domain):
        self.domain = domain
        self.mx = dict()

    def addServ(self, mxk, serv):
        if not self.mx.has_key(mxk):
            self.mx[mxk] = []

        self.mx[mxk].append(serv)

class Database:

    def __init__(self):
        """Initialize the database if the tables have not already been created"""
        self.con = lite.connect('database.db')
        self.cur = self.con.cursor()

        self.cur.execute('SELECT SQLITE_VERSION()')
        data = self.cur.fetchone()
        if DEBUG:
            print "SQlite version %s" % data

        # Create initial tables
        self.cur.execute("CREATE TABLE IF NOT EXISTS Domains(Id INTEGER PRIMARY KEY AUTOINCREMENT, Domain TXT);")
        self.cur.execute("CREATE TABLE IF NOT EXISTS Mx(Id INTEGER PRIMARY KEY AUTOINCREMENT, Domain_id INT, Domain TXT, Priority INT);")
        self.cur.execute("CREATE TABLE IF NOT EXISTS Server(Id INTEGER PRIMARY KEY AUTOINCREMENT, Mx_id INT, IP TXT, ESMTP BIT, TLS BIT, \
                SSL_Ciper_Name TXT, SSL_Cipher_Version TXT, SSL_Cipher_Bits INT, SSL_Verified BIT);")
    
    def __del__(self):
        """Cleanup"""
        if self.con: self.con.close()
    
    def add(self, dom):
        dom_id = self.addDomain(dom.domain)
        for x,y in dom.mx:
            mx_id = self.addMX(dom_id, dom.domain, x['pref'])
            for serv in dom.mx[x]:
                self.addServer(mx_id, serv)

    def addDomain(self, domain):
        """Add domain record
        
        Paramaters:
            domain -- string of domain to add
        Return:
            id of new record
        """

        self.cur.execute("INSERT INTO Domains(Domain) VALUES ('%s');" % domain)
        return self.cur.lastrowid


    def addMX(self, domain_id, domain, priority):
        """Add MX record
        
        Paramaters:
            domain_id -- id of domain record
            domain -- string of domain name
            priority -- priority of mx record
        Return:
            id of new record
        """

        self.cur.execute("INSERT INTO Mx VALUES" \
                "(NULL, %d, '%s', %d);" % (domain_id, domain, priority))
        return self.cur.lastrowid


    def addServer(self, mx_id, serv):
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
