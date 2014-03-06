import sqlite3 as lite
import sys

class database:

    def __init__(self):
        self.con = lite.connect('database.db')
	cur = self.con.cursor()

	cur.execute('SELECT SQLITE_VERSION()')
	data = cur.fetchone()
	print "SQlite version %s" % data

	# Create initial tables
	cur.execute("CREATE TABLE IF NOT EXISTS Domains(Id INTEGER PRIMARY KEY, Domain TXT);")
	cur.execute("CREATE TABLE IF NOT EXISTS Mx(Id INTEGER PRIMARY KEY, Domain_id INT, Domain TXT, Priority INT);")
	cur.execute("CREATE TABLE IF NOT EXISTS Server(Id INTEGER PRIMARY KEY, Mx_id INT, IP TXT, ESMTP BIT, TLS BIT, \
		SSL_Ciper_Name TXT, SSL_Cipher_Version TXT, SSL_Cipher_Bits INT, SSL_Verified BIT);")
	
    def __del__(self):
	if self.con: self.con.close()
	

    def addDomain(self, domain):
	return


    def addMX(self, mx):
	return


    def addServer(self, serv):
	return
