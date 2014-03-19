#!/usr/bin/env python
import sqlite3 as lite
import sys
import pprint

DEBUG = False

class Stats:
    """Extract and format useful statistics"""

    def __init__(self):
        print "\nExtracting statistics from database:"

        """Open the database"""
        self.con = lite.connect(sys.argv[1])
        self.cur = self.con.cursor()

        if DEBUG:
            self.cur.execute('SELECT SQLITE_VERSION()')
            data = self.cur.fetchone()
            print "SQlite version %s" % data

        self.cur.execute("select count(*) from Servers;")
        self.num_servers = int(self.cur.fetchone()[0])
        print "Collected data on %d servers.\n" % self.num_servers
    
    def __del__(self):
        """Cleanup"""
        self.con.commit()
        if self.con: 
            self.con.close()
    
    def get_esmtp(self):
        self.cur.execute("select count(*) from Servers where esmtp = 'True';")
        num_servers_esmtp = int(self.cur.fetchone()[0])

        print "%d servers support esmtp." % num_servers_esmtp
        print "%f%% servers don't support esmtp." % (float(self.num_servers - \
                num_servers_esmtp) / float(self.num_servers) * 100)
        print

    def get_tls(self):
        self.cur.execute("select count(*) from Servers where tls = 'True';")
        num_servers_tls = int(self.cur.fetchone()[0])

        print "%d servers support tls." % num_servers_tls
        print "%f%% servers don't support tls." % (float(self.num_servers - \
                num_servers_tls) / float(self.num_servers) * 100)
        print

    def get_ssl_cert(self):
        self.cur.execute("select count(*) from Servers where ssl_verified = 'True';")
        num_servers_verified = int(self.cur.fetchone()[0])

        print "%d servers have valid certificates." % num_servers_verified
        print "%f%% servers don't have valid certificates." % (float(self.num_servers - \
                num_servers_verified) / float(self.num_servers) * 100)
        print

    def get_top_ten(self):
        topten = ['hotmail.com', 'gmail.com', 'yahoo.com', 'aol.com', 
                'comcast.com', 'mail.ru', 'web.de', 'qq.com', 'gmx.net',
                'naver.com']
        
        print "Domain\tTLS\tVerified\t"
        results = []
        for domain in topten:
            self.cur.execute("select id from domains where domain = '%s';" % domain)
            dom_id = self.cur.fetchone()[0]
            self.cur.execute("select mx_id from domains_mx where domain_id = %s;" % dom_id)
            mx_id = self.cur.fetchone()[0]
            self.cur.execute("select server_id from mx_servers where mx_id = %s;" % mx_id)
            serv_id = self.cur.fetchone()[0]

            self.cur.execute("select tls from servers where id = %s;" % serv_id)
            tls = self.cur.fetchone()[0]
            self.cur.execute("select ssl_verified from servers where id = %s;" % serv_id)
            verified = self.cur.fetchone()[0]
            results.append([domain, tls, verified])

            #num_servers_tls = int(self.cur.fetchone()[0])
            #self.cur.execute("select count(*) from Servers where ssl_verified = 'True';")

        pprint.pprint(results)
            





stats = Stats()
'''
stats.get_esmtp()
stats.get_tls()
stats.get_ssl_cert()
'''
stats.get_top_ten()
