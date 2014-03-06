#!/usr/bin/env python
import sys
import worker_thread
import time

def done(enqueueThread, saveThread, workerThreads):
    if not enqueueThread.done:
        return False
    if worker_thread.working(workerThreads):
        return False
    if saveThread.active:
        return False
    if saveThread.queue.qsize() > 0:
        return False
    #if enqueueThread.domains != saveThread.saved:
    #    return False
    return True


if __name__ == '__main__':
    if len(sys.argv) < 3 or not sys.argv[2].isdigit():
        print "Usage: "+sys.argv[0]+" domain_file number_of_threads"
        sys.exit()

    n = int(sys.argv[2])
    domain_file = sys.argv[1]

    enqueueThread, saveThread, workerThreads, = worker_thread.start(domain_file, n)
    nThreads = len(workerThreads)

    time.sleep(0.6)

    while not done(enqueueThread, saveThread, workerThreads):
        sys.stdout.write( "\rDomains: %d\tSaved: %d\tFailed: %d\tThreads: %d\t" % (enqueueThread.domains, saveThread.saved, worker_thread.getTotalFailures(workerThreads), nThreads ) )
        sys.stdout.flush()
        time.sleep(1)
    
    sys.stdout.write( "\rDomains: %d\tSaved: %d\tThreads: %d\t" % (enqueueThread.domains, saveThread.saved, nThreads ) )
    sys.stdout.flush()

    print "\nDone!"





