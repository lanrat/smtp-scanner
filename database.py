import sqlite3 as lite
import time

DEBUG = False

_ready = False

class DomObject:
    def __init__(self, domain, rank=None):
        domain = domain.lower()
        self.domain = domain
        self.rank = rank
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
            self.cur.execute("CREATE TABLE IF NOT EXISTS domains( \
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT, \
                                                            domain TXT NOT NULL UNIQUE, \
                                                            rank int \
                                                        );")
            self.cur.execute("CREATE TABLE IF NOT EXISTS mx( \
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT, \
                                                            domain TXT NOT NULL UNIQUE, \
                                                            priority INT \
                                                        );")
            self.cur.execute("CREATE TABLE IF NOT EXISTS domains_mx( \
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT, \
                                                            domain_id INT NOT NULL, \
                                                            mx_id INT NOT NULL \
                                                        );")
            self.cur.execute("CREATE TABLE IF NOT EXISTS servers( \
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT, \
                                                            ip TXT NOT NULL, \
                                                            ESMTP BIT, \
                                                            TLS BIT, \
                                                            SSL_Cipher_Name TXT, \
                                                            SSL_Cipher_Version TXT, \
                                                            SSL_Cipher_Bits INT, \
                                                            SSL_Verified BIT \
                                                        );")
            self.cur.execute("CREATE TABLE IF NOT EXISTS mx_servers( \
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT, \
                                                            mx_id INT NOT NULL, \
                                                            server_id INT NOT NULL \
                                                        );")
            #create indexes
            self.cur.execute("CREATE INDEX IF NOT EXISTS domains_name_index on domains (domain);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS domains_rank_index on domains (rank);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS mx_name_index on mx (domain);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS server_ip_index on servers (ip);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS domains_Mx_domain_index on domain_mx (domain_id);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS domains_Mx_mx_index on domains_Mx (mx_id);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS mx_server_mx_index on mx_servers (mx_id);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS mx_server_domain_index on mx_servers (server_id);")
            #commit changes
            self.con.commit()
            global _ready
            _ready = True
        else:
            while not _ready:
                time.sleep(1)

    def __del__(self):
        """Cleanup"""
        try:
            self.con.commit()
            if self.con: 
                self.con.close()
        except:
            pass
 
    def add(self, dom):
        """Add record

        Paramaters:
            dom -- object containing domain, mx list, and server lists
        """

        if dom.mx is None:
            return 
        dom_id = self.add_domain(dom.domain, dom.rank)
        if dom_id == -1:
            return
        for __x, __y in dom.mx.iteritems():
            mx_id, new = self.add_mx(dom_id, __x, __y[0])
            if new:
                for serv in dom.mx[__x][1]:
                    self.add_server(mx_id, serv)
        self.con.commit()

    def check_domain(self, domain):
        domain = domain.lower()
        return self.cur.execute("SELECT id FROM domains WHERE domain = '%s';" \
                % domain).fetchone()

    def add_domain(self, domain, rank=None):
        """Add domain record

        Paramaters:
            domain -- string of domain to add
            rank -- the  domains ranking
        Return:
            id of new record
        """
        domain = domain.lower()
        r = self.check_domain(domain)
        if r is not None:
            return -1
        self.cur.execute("INSERT INTO domains(domain, rank) VALUES ('%s', %d);" \
                % (domain, rank))
        return self.cur.lastrowid


    def check_mx_record(self, domain):
        domain = str(domain).lower()
        return self.cur.execute("SELECT * FROM mx WHERE domain = '%s';" \
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
            self.cur.execute("INSERT INTO mx VALUES" \
                    "(NULL, '%s', %d);" % (domain, priority))
            mx_id = self.cur.lastrowid

        self.cur.execute("INSERT INTO domains_mx VALUES (NULL, %d, %d);" \
                % (domain_id, mx_id))

        return mx_id, new

    def check_server_record(self, ip):
        return self.cur.execute("SELECT * FROM servers WHERE ip = '%s';" \
                % ip).fetchone()

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
        if s is not None:
            serv_id = s[0]
        else:
            new = True
            self.cur.execute("INSERT INTO servers VALUES" \
                    "(NULL, '%s', '%s', '%s', '%s', '%s', '%s', '%s');" \
                    % (serv.ip, serv.esmtp, serv.tls, \
                    serv.ssl_cipher_name, serv.ssl_cipher_version, \
                    serv.ssl_cipher_bits, serv.ssl_verified))
            serv_id = self.cur.lastrowid

        self.cur.execute("INSERT INTO mx_servers VALUES (NULL, %d, %d);" \
                % (mx_id, serv_id))

        return serv_id
