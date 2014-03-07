#!/usr/bin/env python
import sqlite3 as lite

DEBUG = False

class Stats:
    """Extract and format useful statistics"""

    def __init__(self):
        """Open the database"""
        self.con = lite.connect('/scratch/test_run/data.db')
        self.cur = self.con.cursor()

        if DEBUG:
            self.cur.execute('SELECT SQLITE_VERSION()')
            data = self.cur.fetchone()
            print "SQlite version %s" % data
    
    def __del__(self):
        """Cleanup"""
        self.con.commit()
        if self.con: 
            self.con.close()
    
    def get_esmtp(self):
        self.cur.execute("select count(*) from Server;")
        num_servers = int(self.cur.fetchone()[0])
        self.cur.execute("select count(*) from Server where esmtp = 'True';")
        num_servers_esmtp = int(self.cur.fetchone()[0])

        print "Collected data on %d servers." % num_servers
        print "%d servers support esmtp." % num_servers_esmtp
        print "%f%% servers don't support esmtp." % (float(num_servers - \
                num_servers_esmtp) / float(num_servers) * 100)

stats = Stats()
stats.get_esmtp()
