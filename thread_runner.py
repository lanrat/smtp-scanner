#!/usr/bin/env python
import sys
import worker_thread
import time
import datetime


start_time = 0
last_done = 0

UPDATE_DELAY = 1

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

def printStatus(domains, saved, failed, nTthreads):
    global start_time, last_done
    running_seconds = (time.time() - start_time)
    running_time = str(datetime.timedelta(seconds=int(running_seconds)))
    lps = round((saved-last_done)/UPDATE_DELAY, 2)

    last_done = saved

    sys.stdout.write( "\rDomains: %d\tSaved: %d\tFailed: %d\tThreads: %d\tLPS: %.1f\tTime: %s" %
            (domains, saved, failed, nThreads, lps, running_time) )
    sys.stdout.flush()


if __name__ == '__main__':
    if len(sys.argv) < 3 or not sys.argv[2].isdigit():
        print "Usage: "+sys.argv[0]+" domain_file number_of_threads"
        sys.exit()

    n = int(sys.argv[2])
    domain_file = sys.argv[1]

    start_time = time.time()

    enqueueThread, saveThread, workerThreads, = worker_thread.start(domain_file, n)
    nThreads = len(workerThreads)

    time.sleep(0.6)

    while not done(enqueueThread, saveThread, workerThreads):
        printStatus(enqueueThread.domains, saveThread.saved, worker_thread.getTotalFailures(workerThreads), nThreads)
        
        time.sleep(UPDATE_DELAY)

    printStatus(enqueueThread.domains, saveThread.saved, worker_thread.getTotalFailures(workerThreads), nThreads)

    print "\nDone!"





