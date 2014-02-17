import re
import sys
import dns.resolver

# Default resolver
resolver = dns.resolver.Resolver()


"""
Function: set_nameservers
Description: Sets nameservers field of a Resolver object.  If res is not
             defined, sets the nameservers field of the default resolver.
Parameters:
      servers - a list of IPv4 addresses (in string form) for DNS servers
      res (optional) - a Resolver object to set nameservers for
"""
def set_nameservers(servers, res=resolver):
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
def mx_lookup(domain, nameservers=None):

    res = resolver

    # Create new resolver if nameservers is specified
    if nameservers is not None:
        res = dns.resolver.Resolver()
        set_nameservers(nameservers, res)

    # Get MX records for domain
    records = res.query(domain, 'MX')
    # Sort by preference
    sortRecords = sorted(records, key=lambda rec: rec.preference)

    lastPref = -1
    ipList = []
    for rec in sortRecords:
        if rec.preference > lastPref:
            lastPref = rec.preference
            ip = res.query(rec.exchange, 'A')
            if ip is not None:
                ipList.append(ip[0].address)
                print "Host: %s, Preference: %s" % (rec.exchange, rec.preference)
                print "\t%s" % ip[0].address

    return ipList
