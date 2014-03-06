#!/usr/bin/env python
import sys
import worker_thread
import time

SLEEP_TIME = 1

def done(enqueueThread, saveThread, workerThreads):
    print "a"
    if not enqueueThread.done:
        return False
    print "a"
    if worker_thread.working(workerThreads):
        return False
    print "a"
    if saveThread.active:
        return False
    print "a"
    if saveThread.queue.qsize() > 0:
        return False
    print "a"
    return True


if __name__ == '__main__':
    if len(sys.argv) < 3 or not sys.argv[2].isdigit():
        print "Usage: "+sys.argv[0]+" domain_file number_of_threads"
        sys.exit()
    
    n = int(sys.argv[2])
    domain_file = sys.argv[1]

    enqueueThread, saveThread, workerThreads, = worker_thread.start(domain_file, n)
    nThreads = len(workerThreads)

    print "pre"
    time.sleep(0.5)
    print "port"

    while not done(enqueueThread, saveThread, workerThreads):
        sys.stdout.write( "\rDomains: %d\tSaved: %d\tThreads: %d\t" % (enqueueThread.domains, saveThread.saved, nThreads ) )

        time.sleep(SLEEP_TIME)

    print "\nDone!"





