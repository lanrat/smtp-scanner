import sqlite3 as lite
import sys

class database:

    def __init__(self):
        """Initialize the database if the tables have not already been created"""
        self.con = lite.connect('database.db')
        self.cur = self.con.cursor()

        self.cur.execute('SELECT SQLITE_VERSION()')
        data = self.cur.fetchone()
        print "SQlite version %s" % data

        # Create initial tables
        self.cur.execute("CREATE TABLE IF NOT EXISTS Domains(Id INTEGER PRIMARY KEY, Domain TXT);")
        self.cur.execute("CREATE TABLE IF NOT EXISTS Mx(Id INTEGER PRIMARY KEY, Domain_id INT, Domain TXT, Priority INT);")
        self.cur.execute("CREATE TABLE IF NOT EXISTS Server(Id INTEGER PRIMARY KEY, Mx_id INT, IP TXT, ESMTP BIT, TLS BIT, \
                SSL_Ciper_Name TXT, SSL_Cipher_Version TXT, SSL_Cipher_Bits INT, SSL_Verified BIT);")
    
    def __del__(self):
        """Cleanup"""
        if self.con: self.con.close()
    

    def addDomain(self, domain):
        """Add domain record
        
        Arguments:
            domain -- string of domain to add
        Return:
            id of new record
        """

        self.cur.execute("INSERT INTO Domains(Domain) VALUES ('%s');" % domain)
        return self.cur.lastrowid


    def addMX(self, mx):
        return


    def addServer(self, serv):
        return
