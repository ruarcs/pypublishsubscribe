from threading import Thread
from Queue import Queue
import unittest
import requests
from basepublishsubscribetest import BasePublishSubscribeTest

class LoadTest(BasePublishSubscribeTest):
    """A set of tests to ensure that the Publish-Subscribe
        server copes under simulated load.
        """  
    def testSimpleLoadTestNoSubscription(self):
        def sendRequestExpect404():
            response = requests.get("http://localhost:%d/weather/alice" % self.port)
            self.assertEqual(response.status_code, 404)
        concurrent = 100
        q = Queue(concurrent * 2)
        threads = []
        for i in range(concurrent):
            t = Thread(target=sendRequestExpect404)
            t.daemon = True
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()
            
    def testSimpleLoadTestWithSubscription(self):
        def sendRequestExpect200():
            response = requests.get("http://localhost:%d/weather/alice" % self.port)
            self.assertEqual(response.status_code, 200)
            response = requests.post("http://localhost:%d/weather/alice" % self.port, data='')
            self.assertEqual(response.status_code, 200)
            concurrent = 100
            for i in range(concurrent):         
                response = requests.post("http://localhost:%d/weather" % self.port, data='cloudy')
                self.assertEqual(response.status_code, 200)
            q = Queue(concurrent * 2)
            threads = []
            for i in range(concurrent):
                t = Thread(target=sendRequestExpect200)
                t.daemon = True
                t.start()
                threads.append(t)
            for thread in threads:
                thread.join()
            
if __name__ == '__main__':
    unittest.main()