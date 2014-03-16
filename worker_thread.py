import threading
from mx_lookup import *
from Queue import Queue
import queue_threads
import smtp_scanner
import database
import traceback #for dEBUG
import database

MAX_QUEUE_SIZE = 10000

def get_nameservers_from_file():
    names = []
    f = open('nameservers', 'r')
    for line in f:
        names.append(line.strip())
    f.close()
    return names


def working(threads):
    ''' returns true if any of the threads are active '''
    if not threads:
        return
    for thread in threads:
        if thread.active:
            return True
    return False

def getFailures(threads):
    ''' returns the total count of the failure types'''
    if not threads:
        return 0, 0, 0
    exception_failures = 0
    smtp_failures = 0
    domain_failures = 0
    for thread in threads:
        exception_failures += thread.exception_failures
        smtp_failures += thread.smtp_failures
        domain_failures += thread.domain_failures
    return domain_failures, exception_failures, smtp_failures

def getTotalFailures(threads):
    ''' returns the sum of all failures ( not smtp)'''
    domf, excf, smtpf = getFailures(threads)
    return domf + excf


def start(domain_file, n=1):
    '''read domains from domain_file and then starts n worker threads'''
    if n < 1:
        print "Must create at lest one thread!!!!"
        return

    nameservers = get_nameservers_from_file()
    domain_queue = Queue(maxsize=MAX_QUEUE_SIZE)
    save_queue = Queue(maxsize=MAX_QUEUE_SIZE)

    enqueueThread = queue_threads.Enqueue(domain_queue, domain_file)
    enqueueThread.start()
    saveThread = queue_threads.Save(save_queue)
    saveThread.start()

    workerThreads = list()

    for i in range(n):
        t = Worker(domain_queue, save_queue, nameservers)
        t.start()
        workerThreads.append(t)

    return enqueueThread, saveThread, workerThreads


class Worker(threading.Thread):
    ''' this is the main worker threads that we will spawn multiples of to do all the work'''

    def __init__(self, domain_queue, save_queue, nameservers, check_db=True):
        threading.Thread.__init__(self)
        self.daemon = True
        self.domain_queue = domain_queue
        self.save_queue = save_queue
        self.mxdef = MXLookup(nameservers, roundRobin=True)
        self.running = False
        self.done = False
        self.work_done = 0
        self.active = False
        self.domain_failures = 0
        self.exception_failures = 0
        self.smtp_failures = 0
        self.scanner = smtp_scanner.smtp_scanner()
        self.db = None
        self.check_db = check_db

    def run(self):
        ''' main loop for worker thread'''
        if self.check_db:
            self.db = database.Database()

        self.running = True

        while True:
            self.active = False
            domain = self.domain_queue.get()
            if domain:
                self.active = True

                if self.db and self.db.check_domain(domain):
                    continue

                try:
                    mxList = self.mxdef.mx_lookup(domain, all_mx=True, all_ip=True)
                    if not mxList:
                        self.domain_failures +=1
                        continue

                    dom = database.DomObject(domain)
                    for mx in mxList.mxList():
                        pref = mxList.getPref(mx)
                        if self.db and self.db.check_mx_record(mx):
                            dom.add(mx, pref, None) #TODO verify this
                            continue
                        for ip in mxList.ipList(mx):
                            if self.db and self.db.check_server_record(ip):
                                dom.add(mx, pref, smtp_scanner.smtp_server(ip)) #TODO verify this
                                continue
                            serv = self.scanner.queryServer(ip)
                            if serv:
                                #add result to some struct
                                dom.add(mx, pref, serv)
                            else:
                                self.smtp_failures +=1


                    #save something
                    self.save_queue.put(dom)
                    self.work_done += 1

                except Exception as e:
                    self.exception_failures += 1
                    print "Exception on domain: "+domain
                    print e
                    traceback.print_exc()

            self.domain_queue.task_done()

        self.done = True
        self.running = False

