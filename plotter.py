import sys
import re
from pylab import *
from PIL import *
from PIL import Image
import numpy as np
import getopt
from matplotlib.font_manager import FontProperties

if len(sys.argv) < 3:
    print "Please specify an input file and graph header (in quotes)"
    sys.exit(1)

(opts, args) = getopt.getopt(sys.argv[1:], "xys", ["ymin=", "ymax=", "xmin=", "xmax=", "bx=", "by=", "small"])

xLog = False
yLog = False
scale = False
xMin = None
yMin = None
xMax = None
yMax = None
bx = None
by = None
small = False
for o, v in opts:
    if o == '-s':
        scale = True
    elif o == '-x':
        xLog = True
    elif o == '-y':
        yLog = True
    elif o == "--ymin":
        yMin = float(v)
    elif o == "--ymax":
        yMax = float(v)
    elif o == "--xmin":
        xMin = float(v)
    elif o == "--xmax":
        xMax = float(v)
    elif o == "--bx":
        bx = float(v)
    elif o == "--by":
        by = float(v)
    elif o == "--small":
        small = True
    else:
        assert False, "Unhandled option %s" % o

bbox = None
if bx is not None and by is not None:
    bbox=(bx, by)


inFile = open(args[0])
header = args[1]
headerPattern = re.compile("=[ ]*%s[ ]*=" % header.lower())
anyHeaderPattern = re.compile("=.*=")

state = 0       # 0: Haven't found section, 1: currently processing section
rank = []
rankLen = 0
series = {}
#seriesPct = {}
seriesKeys = []
totals = None
for line in inFile:
    line = line.rstrip("\n")
    if anyHeaderPattern.search(line.lower()):
        if headerPattern.search(line.lower()):
            state = 1
            print "%s" % line
        elif state == 1:
            break

    elif state == 1:
        fields = line.split("\t")
        if fields[-1] == "":
            fields = fields[:-1]
        if len(fields) == 0:
            continue
        elif fields[0].upper() == 'RANK':
            rank = fields[1:]
            rankLen = len(rank)
            totals = [0] * rankLen
        elif fields[0] == "" or fields[0][0] == '#':
            continue
        elif len(fields[1:]) == rankLen:
            print "Key: %s" % fields[0]
            series[fields[0]] = fields[1:]
            seriesKeys.append(fields[0])
            for i in range (0, len(series[fields[0]])):
                try:
                    totals[i] += float(series[fields[0]][i])
                except:
                    series[fields[0]][i] = 0
                    pass
        else:
            print "Row (%s) does not have same number of fields (%d) as rank (%d) " % (fields[0], len(fields[1:]), len(rank))
            sys.exit(1)


inFile.close()


fig = figure()
suptitle(header)

for key in seriesKeys:
    y = []
    for a, b in zip(series[key], totals):
        try:
            val = float(a) / float(b)
        except:
            val = 0.
        y.append( val )
    x = rank
    if xLog:
        x = [math.log(float(a), 10) for a in x]
    try:
        plot(x, y, label="%s" % key)
    except:
        print "Key: %s" % key
        raise

xlim([xMin, xMax])
ylim([yMin, yMax])
xlabel("Rank")
ylabel("Pct of domains")
fp = None
if small:
    fp = FontProperties()
    fp.set_size('small')
if bbox is not None:
    legend(loc="upper left", prop = fp, bbox_to_anchor=bbox)
else:
    legend(loc="upper left", prop = fp)
show()
