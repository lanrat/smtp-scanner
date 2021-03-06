#!/usr/bin/env python

import re
import sys
import dns.resolver
import dns.rdtypes.ANY.MX

DEBUG = False

class MXResult:

    def __init__(self, domain, all_mx=False, all_ip=False):
        self.domain = domain
        self.all_mx = all_mx
        self.all_ip = all_ip
        self.mx = {}

    def addMx(self, mx, pref):
        if self.mx.get(mx) is None:
            self.mx[mx] = {}
            self.mx[mx]['pref'] = pref

    def addIPList(self, mx, ipList):
        if self.mx[mx].get('ip') is None:
            self.mx[mx]['ip'] = []

        self.mx[mx]['ip'].append(ipList)

    def getPref(self, mx):
        return self.mx[mx]['pref']

    def mxList(self):
        try:
            #mxRecords = sorted(self.mx, key=lambda mx:"%s%s" % (mx['pref'], mx))
            mxRecords = sorted(self.mx)
            return mxRecords
        except:
            raise
            return None

    def ipList(self, mx):
        try:
            if self.all_ip:
                return self.mx[mx]['ip']
            else:
                return [self.mx[mx]['ip'][0]]
        except:
            return []
        

    def __repr__(self):
        printStr =  "Domain: %s\n" % self.domain

        lastPref = -1
        for mx in self.mxList():
            if self.all_mx or lastPref < self.mx[mx]['pref']:
                lastPref = self.mx[mx]['pref']
                printStr += "  MX: %s\n" % mx
                printStr += "  Pref: %s\n" % self.mx[mx]['pref']
                printStr += "  IP Addresses:\n"

                for ip in self.ipList(mx):
                    printStr += "    %s\n" % ip
                    if not self.all_ip:
                        break

        return printStr

class MXLookup:

    def __init__(self, nameservers=None, roundRobin=False):
        # Default resolver
        self.resolver = dns.resolver.Resolver()

        # Nameservers 
        self.roundRobin = roundRobin
        self.nextServer = 0
        self.nameservers = []
        if nameservers is not None:
            self.nameservers = nameservers

    """
    Function: set_nameservers
    Description: Sets nameservers field of a Resolver object.  If res is not
                 defined, sets the nameservers field of the default resolver.
    Parameters:
          servers - a list of IPv4 addresses (in string form) for DNS servers
          res (optional) - a Resolver object to set nameservers for
    """
    def set_nameservers(self, servers, res=None):

        if res is None:
            res = self.resolver

        # Make sure servers is iterable and each item is an IPv4 address
        try:
            pattern = re.compile("[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}")
            for s in servers:
                if not pattern.match(s):
                    sys.stderr.write("(%s) is not a valid IP address\n" % s)
                    return

        # servers not formatted correctly -- raise exception
        except:
            sys.stderr.write("Unable to set name servers\n")
            raise
        
        # Set name servers of our DNS resolver
        res.nameservers = servers

    """
    Function: get_mx_records
    Description: Queries DNS servers to get MX records for domain.  Returns a
                 list sorted by preference.
    Parameters:
        domain - domain name to look up MX records for
        res (optional) - Resolver object to use in query
    Returns:    List of MX records for domain, sorted by preference
    """
    def get_mx_records(self, domain, res=None):
        if res is None:
            res = self.resolver

        # Get MX records for domain
        for _ in range(1, 5):
            try:
                records = res.query(domain, 'MX')
                # Sort by preference
                return sorted(records, key=lambda rec: rec.preference)
            except (dns.resolver.Timeout, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                self.mx_round_robin()
            except dns.resolver.NoAnswer:
                return [dns.rdtypes.ANY.MX.MX(rdclass=1, rdtype=15, \
                                              exchange=domain, preference=-1)]
        self.mx_round_robin()

        return None

    """
    Function: mx_round_robin
    Description: Sets resolver to next nameserver in round robin.
    Returns: DNS resolver set to next nameserver
    """
    def mx_round_robin(self, remove=False):
        res = self.resolver

        if self.roundRobin:
            # remove failed nameserver
            if remove:
                del self.nameservers[self.nextServer]
            else:
                self.nextServer = self.nextServer + 1
            if self.nextServer >= len(self.nameservers):
                self.nextServer = 0
            
            if len(self.nameservers) == 0:
                print "All nameservers have failed."
                sys.exit(0)

            res = dns.resolver.Resolver()
            self.set_nameservers([self.nameservers[self.nextServer]], res)
            if DEBUG:
                print "Using nameserver: %s" % (self.nameservers[self.nextServer])

        return res


    """
    Function: mx_lookup
    Description: Looks up the MX records for domain.  If nameservers is specified,
                 attempts to use those, otherwise uses default name servers.
                 Returns list of IPv4 addresses, one per preference level.
    Parameters:
          domain - domain name to look up MX records for
          nameservers (optional) - list of IPv4 addresses for DNS server to use
                                   for this lookup only
    Returns:  List of IPv4 addresses of MX records for domain, sorted by
              preference, low to high.  Returns one IP per preference level.
    """
    def mx_lookup(self, domain, nameservers=None, all_mx=False, all_ip=False):

        res = self.resolver

        # Create new resolver if nameservers is specified
        if nameservers is not None:
            res = dns.resolver.Resolver()
            self.set_nameservers(nameservers, res)

        # Get records and remove bad nameservers
        try:
            sortRecords = self.get_mx_records(domain, res)
        except:
            #invalid domain name
            return None

        if sortRecords is None:
            return None

        mxResult = MXResult(domain, all_mx, all_ip)

        # Go through each of the MX records
        for rec in sortRecords:
            if DEBUG:
                print "%s" % (rec.exchange)
            mxResult.addMx(rec.exchange, rec.preference)
            try:
                ip = res.query(rec.exchange, 'A')
            except:
                ip = None

            if ip is not None:
                # Sort the results so we always get the same IP address
                ip = sorted(ip, key=lambda addr: addr.address)
                for i in ip:
                    mxResult.addIPList(rec.exchange, i.address)

                if DEBUG:
                    if rec.exchange == domain:
                        print ">>> NO MX RECORD FOUND <<<-----------------------"
                    print "Host: %s, Preference: %s" % \
                            (rec.exchange, rec.preference)
                    print "\t%s" % ip[0].address

        return mxResult


    def __del__(self):
        # save list of good nameservers
        '''f = open("good_nameservers", "w")
        for name in self.nameservers:
            f.write(name + '\n')
        f.close()'''



if __name__ == "__main__":
    DEBUG = True
    mx = MXLookup(['8.8.8.8'])
    try:
        line = raw_input("Domain: ")
        while line is not None:
            line = line.replace("\n", "")
            print ">>>>>_____ %s _____<<<<<" % line
            mx.mx_lookup(line)
            line = raw_input("Domain: ")
    except EOFError:
        pass
