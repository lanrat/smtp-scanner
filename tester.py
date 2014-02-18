import sys
from smtp_scanner import *
from mx_lookup import *

if len(sys.argv) != 2:
    print "Please specify a file containing a newline-separated list of domains"
    exit(1)

mxdef = MXLookup()
mxgoogle = MXLookup(['8.8.8.8'])

fd = open(sys.argv[1])

scanner = smtp_scanner()

for line in fd:
    line = line.replace("\n", "")
    print ">>>---- %s ----<<<" % line
    ipList = mxdef.mx_lookup(line)
    for ip in ipList:
        print scanner.queryServer(ip)
        print "==========================================="

    print "\n"

fd.close()
