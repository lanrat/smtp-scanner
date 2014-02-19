#!/usr/bin/env python
import sys
from smtp_scanner import *
from mx_lookup import *

if len(sys.argv) != 2:
    print "Please specify a file containing a newline-separated list of domains"
    exit(1)

'''
Bind server is up and running on 127.0.0.1
Still need to add all zones. The zone file I tested was small. 
I'm not sure how well it will work with larger zone files like com and net
'''
mxdef = MXLookup()
mxgoogle = MXLookup(['8.8.8.8'])

fd = open(sys.argv[1])

to = 5
scanner = smtp_scanner()

esmtp = {}
esmtp[True] = []
esmtp[False] = []

tls = {}
tls[True] = []
tls[False] = []

ssl = {}
ssl[True] = []
ssl[False] = []

cert = {}
cert[True] = []
cert[False] = []

for line in fd:
    line = line.replace("\n", "")
    print ">>>---- %s ----<<<" % line
    ipList = mxdef.mx_lookup(line, includepref=True)
    for pref in sorted(ipList.keys()):
        ip = ipList[pref]
        serv = scanner.queryServer(ip, timeout=to)
        if serv is not None:
            esmtp[serv.esmtp == True].append("%s:%s" % (line, pref))
            tls[serv.tls == True].append("%s:%s" % (line, pref))
            ssl[serv.ssl_cipher_name != None].append("%s:%s" % (line, pref))
            cert[serv.ssl_cert != None].append("%s:%s" % (line, pref))
            
        print serv
        print "==========================================="

    print "\n"

fd.close()

print "ESMTP\n\tSupport: %d\n" % len(esmtp[True]), esmtp[True]
print "\tDon't support: %d" % len(esmtp[False]), esmtp[False]

print "TLS\n\tSupport: %d" % len(tls[True]), tls[True]
print "\tDon't support: %d" % len(tls[False]), tls[False]

print "SSL\n\tSupport: %d" % len(ssl[True]), ssl[True]
print "\tDon't support: %d" % len(ssl[False]), ssl[False]

print "Certs\n\tValid: %d" % len(cert[True]), cert[True]
print "\tInvalid: %d" % len(cert[False]), cert[False]
