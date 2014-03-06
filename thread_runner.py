#!/usr/bin/env python
import sys
import worker_thread
import time

SLEEP_TIME = 1

def done(enqueueThread, saveThread, workerThreads):
    if not enqueueThread.done:
        return False
    if worker_thread.working(workerThreads):
        return False
    if saveThread.active:
        return False
    if saveThread.queue.qsize() > 0:
        return False
    return True




if __name__ == '__main__':
    if len(sys.argv) < 3 or not sys.argv[2].isdigit():
        print "Usage: "+sys.argv[0]+" domain_file number_of_threads"
    
    n = int(sys.argv[2])
    domain_file = sys.argv[1]

    enqueueThread, saveThread, workerThreads, = worker_thread.start(domain_file, n)
    nThreads = len(workerThreads)

    while not done(enqueueThread, saveThread, worker_thread):
        sys.stdout.write( "\rDomains: %d\tSaved: %d\tThreads: %d\t" % (enqueueThread.domains, saveThread.saved, nThreads ) )

        time.sleep(SLEEP_TIME)

    print "Done!"





