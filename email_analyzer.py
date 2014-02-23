import sys
import re
import getopt

left = "\x1b[15D"

(opts, args) = getopt.getopt(sys.argv[1:], "", ['limit='])

if len(args) <= 0:
    print "Please specify a text file to read"
    exit()

limit = None
if len(opts) > 0 and opts[0][0] == '--limit':
    limit = int(opts[0][1])

emailFile = open(args[0])

emailDict = {}

sys.stderr.write("\n")
linesRead = 0
emailField = re.compile("^[^|]*\|[^|]*\|([^|]*)\|")
for line in emailFile:
    if (linesRead % 1000) == 0:
        sys.stderr.write("%sLine %d" % (left, linesRead))
    fields = line.split("|")
    if len(fields) < 3:
        continue

    email = fields[2]
    fields = email.split("@")
    if len(fields) < 2:
        continue

    domain = fields[len(fields) - 1]
    if domain.endswith("-"):
        domain = domain[:-1]
    try:
        emailDict[domain] += 1
    except KeyError:
        emailDict[domain] = 1

    linesRead += 1
    if limit is not None and linesRead >= limit:
        break

sys.stderr.write("\n")

print "Total emails: %d" % linesRead
for dom in sorted(emailDict, key = lambda el: -emailDict[el]):
    print "%s" % dom
    print "\t%d" % emailDict[dom]
