import threading
import re
import database

domainRegEx = "[a-zA-Z\d-]{,63}(\.[a-zA-Z\d-]{,63})*$"


class Enqueue(threading.Thread):
    ''' thread to read domains from list and add them to a queue'''

    def __init__(self, queue, filename):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.fileh = open(filename)
        self.running = False
        self.done = False
        self.domains = 0


    def run(self):
        ''' main entrypoint for thread'''
        if not self.fileh:
            print "ERR: unable to open domain list: "+self.filename
            return

        self.running = True

        domainPattern = re.compile(domainRegEx)

        for line in self.fileh:
            line = line.strip()

            if domainPattern.match(line):
                self.queue.put(line)
                self.domains += 1

        self.fileh.close()
        self.running = False
        self.queue.join()
        self.done = True


class Save(threading.Thread):
    '''thread to save all queries as they finish'''

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.running = False
        self.done = False
        self.saved = 0
        self.active = False
        self.db = None
        self.go = True

    def run(self):
        ''' main entrypoint for thread'''
        self.db = database.Database()
        self.running = True

        while self.go:
            self.active = False
            result = self.queue.get()
            if result:
                self.active = True
                self.db.add(result)
                self.saved += 1

            self.queue.task_done()

        self.active = False

        self.done = True
        self.running = False

