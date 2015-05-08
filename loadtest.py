from threading import Thread
from Queue import Queue
import unittest
import requests
from basepublishsubscribetest import BasePublishSubscribeTest

class LoadTest(BasePublishSubscribeTest):
    """A set of tests to ensure that the Publish-Subscribe
        server copes under simulated load.
        """  
            
    def testSimpleLoadTestWithSubscription(self):
        def sendRequestExpect200():
            response = requests.get("http://localhost:%d/weather/alice" % self.port)
            self.assertEqual(response.status_code, 200)
            response = requests.post("http://localhost:%d/weather/alice" % self.port, data='')
            self.assertEqual(response.status_code, 200)
        # Subscribe Alice to weather updates so that messages
        # are persisted when posted.
        response = requests.post("http://localhost:%d/weather/alice" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        self.run_test(100, sendRequestExpect200)
                
    ############################################################################
    # Helper functions
    ############################################################################
        
    def run_test(self, concurrency_level, action):
        for i in range(concurrency_level):         
            response = requests.post("http://localhost:%d/weather" % self.port, data='cloudy')
            self.assertEqual(response.status_code, 200)
        q = Queue(concurrency_level * 2)
        threads = []
        for i in range(concurrency_level):
            t = Thread(target=action)
            t.daemon = True
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()
            
if __name__ == '__main__':
    unittest.main()