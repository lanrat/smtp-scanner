#!/usr/bin/env python
import sys
import worker_thread
import time
import datetime


start_time = 0
last_done = 0

UPDATE_DELAY = 3.0

def done(enqueueThread, saveThread, workerThreads):
    if not enqueueThread.done:
        return False
    if saveThread.active:
        return False
    if worker_thread.working(workerThreads):
        return False
    if saveThread.queue.qsize() > 0:
        return False
    return True

def printStatus(enqueueThread, saveThread, workerThreads):
    global start_time, last_done
    domains = enqueueThread.domains
    saved = saveThread.saved
    nThreads = worker_thread.getActiveThreads(workerThreads)
    sqsize = saveThread.queue.qsize()
    failed = worker_thread.getTotalFailures(workerThreads)

    running_seconds = (time.time() - start_time)
    running_time = str(datetime.timedelta(seconds=int(running_seconds)))
    lps = round((saved-last_done)/UPDATE_DELAY, 2)
    last_done = saved

    sys.stdout.write( "\rDomains: %d\tSaved: %d\tFailed: %d\tThreads: %d\tDPS: %.1f\tTime: %s\tSQS: %d " %
            (domains, saved, failed, nThreads, lps, running_time, sqsize) )
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

    try:
        while not done(enqueueThread, saveThread, workerThreads):
            printStatus(enqueueThread, saveThread, workerThreads)
            time.sleep(UPDATE_DELAY)
        saveThread.queue.join()
    except KeyboardInterrupt:
        print "\n Saving..."
        saveThread.go = False
        while saveThread.active:
            time.sleep(0.2)
        pass
    finally:
        running_seconds = (time.time() - start_time)
        print "\nAverage DPS: "+str(round((saveThread.saved/running_seconds),2))
        domS, mxS, ipS = worker_thread.getSkips(workerThreads)
        print "Domains_Skipped: "+str(domS)+" \tMX_Skipped: "+str(mxS)+" \tIPs_Skipped: "+str(ipS)
        domF, excF, smtpF = worker_thread.getFailures(workerThreads)
        print "Domain_Fails: "+str(domF)+" \tSMTP_Fails: "+str(smtpF)+" \tException_Fails: "+str(excF)

    print "Done!"

