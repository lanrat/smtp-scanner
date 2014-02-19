#!/usr/bin/env python
import sys
from smtp_scanner import *
from mx_lookup import *

if len(sys.argv) != 2:
    print "Please specify a file containing a newline-separated list of domains"
    exit(1)

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

cert = {}
cert[True] = []
cert[False] = []

for line in fd:
    line = line.replace("\n", "")
    print ">>>---- %s ----<<<" % line
    ipList = mxdef.mx_lookup(line)
    for ip in ipList:
        serv = scanner.queryServer(ip, timeout=to)
        if serv is not None:
            esmtp[serv.esmtp == True].append(line)
            tls[serv.tls == True].append(line)
            cert[serv.ssl_cert != None].append(line)
            
        print serv
        print "==========================================="

    print "\n"

fd.close()

print "ESMTP\n\tSupport: %d\n" % len(esmtp[True]), esmtp[True]
print "\tDon't support: %d" % len(esmtp[False]), esmtp[False]

print "TLS\n\tSupport: %d" % len(tls[True]), tls[True]
print "\tDon't support: %d" % len(tls[False]), tls[False]

print "Certs\n\tValid: %d" % len(cert[True]), cert[True]
print "\tInvalid: %d" % len(cert[False]), cert[False]
