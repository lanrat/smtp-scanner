import threading
from mx_lookup import *
from Queue import Queue
import queue_threads
import smtp_scanner

MAX_QUEUE_SIZE = 10000

class domObject:
    def __init__(self, domain):
        self.domain = domain
        self.mx = dict()

    def addServ(self, mx, serv):
        if not self.mx.has_key(mx):
            self.mx[mx] = []

        self.mx[mx].append(serv)


def get_nameservers_from_file():
    names = []
    f = open('nameservers', 'r')
    for line in f:
        names.append(line.strip());
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

    def __init__(self, domain_queue, save_queue, nameservers):
        threading.Thread.__init__(self)
        self.daemon = True
        self.domain_queue = domain_queue
        self.save_queue = save_queue
        self.mxdef = MXLookup(nameservers, roundRobin=True)
        self.running = False
        self.done = False
        self.work_done = 0
        self.active = False
        self.scanner = smtp_scanner.smtp_scanner()

    def run(self):
        ''' main loop for worker thread'''

        self.running = True

        while True:
            self.active = False
            domain = self.domain_queue.get()
            if domain:
                self.active = True

                try:
                    mxList = self.mxdef.mx_lookup(domain, all_mx=True, all_ip=True)
                    if not mxList:
                        #TODO if there are no mx reccords fall back to using A record
                        continue

                    dom = domObject(domain)
                    #TODO some of the mxlist logic makes a little less sense than it should
                    for mx in mxList.mxList():
                        pref = mxList.getPref(mx)
                        for ip in mxList.ipList(mx):
                            serv = self.scanner.queryServer(ip)
                            if not serv:
                                #TODO add result to some struct
                                dom.addServ(mx, serv)

                    #TODO save something
                    self.save_queue.put(dom)

                except IOError as e:
                    #TODO change back to exceptopn
                    print "Exception on domain: "+domain
                    print e

        self.done = True
        self.running = False

