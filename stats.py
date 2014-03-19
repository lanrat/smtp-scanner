#!/usr/bin/env python
import sqlite3 as lite
import sys
from pprint import pprint

DEBUG = False


def print_ld(r,head=True):
    if len(r) < 1:
        return
    keys = r[0].keys()
    if head:
        print '\t'.join(keys)
    for row in r:
        s = ""
        for key in keys:
            s += str(row[key])+'\t'
        print s

class Stats:
    """Extract and format useful statistics"""

    def __init__(self, filename):
        print "\nExtracting statistics from database:"

        """Open the database"""
        self.con = lite.connect(filename)
        self.con.row_factory = self.dict_factory
        self.cur = self.con.cursor()

        if DEBUG:
            self.cur.execute('SELECT SQLITE_VERSION()')
            data = self.cur.fetchone()
            print "SQlite version %s" % data

        self.cur.execute("select count(*) c from Servers;")
        self.num_servers = int(self.cur.fetchone()['c'])
        print "Collected data on %d servers.\n" % self.num_servers

    def __del__(self):
        """Cleanup"""
        self.con.commit()
        if self.con: 
            self.con.close()

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


    def get_esmtp(self):
        self.cur.execute("select count(*) c from Servers where esmtp = 'True';")
        num_servers_esmtp = int(self.cur.fetchone()['c'])

        print "%d servers support esmtp." % num_servers_esmtp
        print "%f%% servers don't support esmtp." % (float(self.num_servers - \
                num_servers_esmtp) / float(self.num_servers) * 100)
        print

    def get_tls(self):
        self.cur.execute("select count(*) c from Servers where tls = 'True';")
        num_servers_tls = int(self.cur.fetchone()['c'])

        print "%d servers support tls." % num_servers_tls
        print "%f%% servers don't support tls." % (float(self.num_servers - \
                num_servers_tls) / float(self.num_servers) * 100)
        print

    def get_ssl_cert(self):
        self.cur.execute("select count(*) c from Servers where ssl_verified = 'True';")
        num_servers_verified = int(self.cur.fetchone()['c'])

        print "%d servers have valid certificates." % num_servers_verified
        print "%f%% servers don't have valid certificates." % (float(self.num_servers - \
                num_servers_verified) / float(self.num_servers) * 100)



    def top_ip_domain(self, limit=20):
        self.cur.execute("select servers.ip, count(domains_mx.domain_id) num from mx_servers, servers, mx, domains_mx where domains_mx.mx_id = mx.id and mx.id = mx_servers.mx_id and servers.id = mx_servers.server_id group by servers.id order by num desc limit %d;" % (limit));
        print_ld(self.cur.fetchall())

    def top_mx(self,limit=20):
        self.cur.execute("select mx.domain, count(domains_mx.mx_id) num from domains_mx, mx where mx.id = domains_mx.mx_id group by domains_mx.mx_id order by num desc limit %d;" % (limit))
        print_ld(self.cur.fetchall())

    def print_top_domain_info(self, limit=10):
        self.cur.execute("select domain domain from domains order by rank asc limit %d;" % (limit))
        l = self.cur.fetchall()
        print " === top %d domains === " % limit
        first = True
        for r in l:
            dom = r['domain']
            print dom
            r = self.get_domain_stats(dom)
            #pprint(r)
            print_ld(r, first)
            first = False
        print ""


    def get_domain_stats(self,domain):
        self.cur.execute("select servers.esmtp, servers.tls, servers.ssl_verified, servers.ssl_ciper_name, servers.ssl_cipher_bits from servers, mx, mx_servers, domains, domains_mx where domains_mx.domain_id = domains.id and domains_mx.mx_id = mx.id and mx_servers.server_id = servers.id and mx_servers.mx_id = mx.id and domains.domain = '%s' group by servers.esmtp, servers.tls, servers.ssl_ciper_name, servers.ssl_cipher_bits, servers.ssl_verified;" % (domain))
        return self.cur.fetchall()

    def get_rank_stats_tls(self,rank=10):
        self.cur.execute("select tls, count(tls) num from (select servers.tls tls from domains join domains_mx on domains.id = domains_mx.domain_id join mx_servers on mx_servers.mx_id = domains_mx.mx_id join servers on servers.id = mx_servers.server_id where domains.rank <= %d group by domains_mx.domain_id order by domains.rank) group by tls order by num desc;" % (rank))
        return self.cur.fetchall()

    def get_rank_stats_esmtp(self,rank=10):
        self.cur.execute("select esmtp, count(esmtp) num from (select servers.esmtp esmtp from domains join domains_mx on domains.id = domains_mx.domain_id join mx_servers on mx_servers.mx_id = domains_mx.mx_id join servers on servers.id = mx_servers.server_id where domains.rank <= %d group by domains_mx.domain_id order by domains.rank) group by esmtp order by num desc;" % (rank))
        return self.cur.fetchall()

    def get_rank_stats_verified(self,rank=10):
        self.cur.execute("select verified, count(verified) num from (select servers.ssl_verified verified from domains join domains_mx on domains.id = domains_mx.domain_id join mx_servers on mx_servers.mx_id = domains_mx.mx_id join servers on servers.id = mx_servers.server_id where domains.rank <= %d group by domains_mx.domain_id order by domains.rank) group by verified order by num desc;" % (rank))
        return self.cur.fetchall()

    def get_rank_stats_cipher(self,rank=10):
        self.cur.execute("select cipher, count(cipher) num from (select servers.ssl_ciper_name cipher from domains join domains_mx on domains.id = domains_mx.domain_id join mx_servers on mx_servers.mx_id = domains_mx.mx_id join servers on servers.id = mx_servers.server_id where domains.rank <= %d group by domains_mx.domain_id order by domains.rank) group by cipher order by num desc;" % (rank))
        return self.cur.fetchall()

    def build_cipher_rank_graph(self, limit, step=10):
        print "=== rank cipher ==="
        i = step
        l = list()
        while i <= limit:
            l.append(self.get_rank_stats_cipher(i))
            i +=step
        if len(l) < 1:
            return
        options = list()
        for i in l:
            for r in i:
                if r['cipher'] not in options:
                    options.append(r['cipher'])
        options.sort()
        '''print header'''
        j = step
        s = "RANK\t"
        while j <= limit:
            s += str(j)+'\t'
            j += step
        print s
        for op in options:
            s = str(op)+'\t'
            for i in l:
                for d in i:
                    if d['cipher'] == op:
                        s += str(d['num'])
                s +='\t'
            print s
        print ""


    def build_tls_rank_graph(self, limit, step=10):
        print "=== rank tls ==="
        i = step
        l = list()
        while i <= limit:
            l.append(self.get_rank_stats_tls(i))
            i +=step
        if len(l) < 1:
            return
        options = list()
        for i in l:
            for r in i:
                if r['tls'] not in options:
                    options.append(r['tls'])
        options.sort()
        '''print header'''
        j = step
        s = "RANK\t"
        while j <= limit:
            s += str(j)+'\t'
            j += step
        print s
        for op in options:
            s = str(op)+'\t'
            for i in l:
                for d in i:
                    if d['tls'] == op:
                        s += str(d['num'])
                s +='\t'
            print s
        print ""




    def build_tls_rank_graph(self, limit, step=10):
        print "=== rank tls ==="
        i = step
        l = list()
        while i <= limit:
            l.append(self.get_rank_stats_tls(i))
            i +=step
        if len(l) < 1:
            return
        options = list()
        for i in l:
            for r in i:
                if r['tls'] not in options:
                    options.append(r['tls'])
        options.sort()
        '''print header'''
        j = step
        s = "RANK\t"
        while j <= limit:
            s += str(j)+'\t'
            j += step
        print s
        for op in options:
            s = str(op)+'\t'
            for i in l:
                for d in i:
                    if d['tls'] == op:
                        s += str(d['num'])
                s +='\t'
            print s
        print ""



    def build_tls_rank_graph(self, limit, step=10):
        print "=== rank tls ==="
        i = step
        l = list()
        while i <= limit:
            l.append(self.get_rank_stats_tls(i))
            i +=step
        if len(l) < 1:
            return
        options = list()
        for i in l:
            for r in i:
                if r['tls'] not in options:
                    options.append(r['tls'])
        options.sort()
        '''print header'''
        j = step
        s = "RANK\t"
        while j <= limit:
            s += str(j)+'\t'
            j += step
        print s
        for op in options:
            s = str(op)+'\t'
            for i in l:
                for d in i:
                    if d['tls'] == op:
                        s += str(d['num'])
                s +='\t'
            print s
        print ""

    def build_esmtp_rank_graph(self, limit, step=10):
        print "=== rank esmtp ==="
        i = step
        l = list()
        while i <= limit:
            l.append(self.get_rank_stats_esmtp(i))
            i +=step
        if len(l) < 1:
            return
        options = list()
        for i in l:
            for r in i:
                if r['esmtp'] not in options:
                    options.append(r['esmtp'])
        options.sort()
        '''print header'''
        j = step
        s = "RANK\t"
        while j <= limit:
            s += str(j)+'\t'
            j += step
        print s
        for op in options:
            s = str(op)+'\t'
            for i in l:
                for d in i:
                    if d['esmtp'] == op:
                        s += str(d['num'])
                s +='\t'
            print s
        print ""

    def build_verified_rank_graph(self, limit, step=10):
        print "=== rank verified ssl ==="
        i = step
        l = list()
        while i <= limit:
            l.append(self.get_rank_stats_verified(i))
            i +=step
        if len(l) < 1:
            return
        options = list()
        for i in l:
            for r in i:
                if r['verified'] not in options:
                    options.append(r['verified'])
        options.sort()
        '''print header'''
        j = step
        s = "RANK\t"
        while j <= limit:
            s += str(j)+'\t'
            j += step
        print s
        for op in options:
            s = str(op)+'\t'
            for i in l:
                for d in i:
                    if d['verified'] == op:
                        s += str(d['num'])
                s +='\t'
            print s
        print ""


stats = Stats(sys.argv[1])
stats.get_esmtp()
stats.get_tls()
stats.get_ssl_cert()

#print "=== top IP ==="
stats.top_ip_domain(50)

#print "=== top MX ==="
stats.top_mx()

stats.print_top_domain_info(20)

#stats.build_esmtp_rank_graph(100000,2000)

stats.build_tls_rank_graph(100000,2000)
stats.build_verified_rank_graph(100000,2000)


stats.build_tls_rank_graph(1000000,20000)
stats.build_verified_rank_graph(1000000,20000)

stats.build_cipher_rank_graph(10000,100)

