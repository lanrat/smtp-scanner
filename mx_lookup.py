import re
import sys
import dns.resolver

DEBUG = False

class MXLookup:

    def __init__(self, nameservers=None):
        # Default resolver
        self.resolver = dns.resolver.Resolver()
        if nameservers is not None:
            self.set_nameservers(nameservers);

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
    def mx_lookup(self, domain, nameservers=None, includepref=False):

        res = self.resolver

        # Create new resolver if nameservers is specified
        if nameservers is not None:
            res = dns.resolver.Resolver()
            self.set_nameservers(nameservers, res)

        # Get MX records for domain
        try:
            records = res.query(domain, 'MX')
        except:
            return None
        # Sort by preference
        sortRecords = sorted(records, key=lambda rec: rec.preference)

        if includepref:
            ipList = {}
        else:
            ipList = []

        # Go through each of the MX records
        lastPref = -1
        for rec in sortRecords:

            # Only look at one record per preference
            if rec.preference > lastPref:
                lastPref = rec.preference
                ip = res.query(rec.exchange, 'A')

                # Sort the results so we always get the same IP address
                ip = sorted(ip, key=lambda addr: addr.address)

                if ip is not None:
                    if includepref:
                        ipList[rec.preference] = ip[0].address
                    else:
                        ipList.append(ip[0].address)
                    if DEBUG:
                        print "Host: %s, Preference: %s" % \
                                                (rec.exchange, rec.preference)
                        print "\t%s" % ip[0].address

        return ipList


if __name__ == "__main__":
    DEBUG = True
    mx = MXLookup()
    try:
        line = raw_input("Domain: ")
        while line is not None:
            line = line.replace("\n", "")
            print ">>>>>_____ %s _____<<<<<" % line
            mx.mx_lookup(line)
            line = raw_input("Domain: ")
    except EOFError:
        pass
