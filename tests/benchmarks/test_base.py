import os
import requests
import threading
import time

from Queue import Queue
from test_support import unittest

test_queue = Queue()

def worker(ident, url, queue, eventFlag):
    #eventFlag.wait()
    start = time.clock()
    r = requests.get(url)
    end = time.clock()
    queue.put((ident, r.status_code, end - start))
    eventFlag.set()
    #queue.task_done()

class HTTPBenchmarkTestCase(unittest.TestCase):
    
    url = 'http://localhost/benchmark/'
    threads = 5

    def setUp(self):
        self.eventFlag = threading.Event()

    def tearDown(self):
        pass

    def test_benchmark_concurrency(self):

        for i in range(self.threads):
            t = threading.Thread(target=worker, args=(i, self.url, test_queue, self.eventFlag))
            #t.daemon = True
            t.start()
            #self.eventFlag.clear()
            obj = test_queue.get()
            print obj
        #test_queue.join()

    

