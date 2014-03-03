#!/usr/bin/env python
import sys
from smtp_scanner import *
from mx_lookup import *

if len(sys.argv) != 2:
    print "Please specify a file containing a newline-separated list of domains"
    exit(1)

mxdef = MXLookup()
mxgoogle = MXLookup(['8.8.8.8'])

# Set round robin for nameservers
# TODO: Modify this to take a file input of nameservers
mxdef = MXLookup(['8.8.8.8', '0.0.0.0', '8.8.4.4'], roundRobin=True)

names = []
f = open('nameservers', 'r')
for line in f:
    names.append(line.strip());
f.close
mxdef = MXLookup(names, roundRobin=True)

fd = open(sys.argv[1])

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
    mxList = mxdef.mx_lookup(line, all_mx=True, all_ip=True)
    for mx in mxList.mxList():
        pref = mxList.getPref(mx)
        for ip in mxList.ipList(mx):
            serv = scanner.queryServer(ip)
            if serv is not None:
                esmtp[serv.esmtp == True].append("%s:%s" % (line, pref))
                tls[serv.tls == True].append("%s:%s" % (line, pref))
                ssl[serv.ssl_cipher_name != None].append("%s:%s" % (line, pref))
                cert[serv.ssl_cert != None].append("%s:%s" % (line, pref))
                
            print "%s : %s" % (mx, pref)
            print serv
            print "==========================================="

    print "\n"

fd.close()

if False:
    print "ESMTP\n\tSupport: %d\n" % len(esmtp[True]), esmtp[True]
    print "\tDon't support: %d" % len(esmtp[False]), esmtp[False]

    print "TLS\n\tSupport: %d" % len(tls[True]), tls[True]
    print "\tDon't support: %d" % len(tls[False]), tls[False]

    print "SSL\n\tSupport: %d" % len(ssl[True]), ssl[True]
    print "\tDon't support: %d" % len(ssl[False]), ssl[False]

    print "Certs\n\tValid: %d" % len(cert[True]), cert[True]
    print "\tInvalid: %d" % len(cert[False]), cert[False]
