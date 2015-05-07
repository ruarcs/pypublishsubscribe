import unittest
import requests
from publishsubscribe import PublishSubscribeResource
from twisted.web import server
from twisted.internet import reactor
from threading import Thread
from Queue import Queue

class CorrectnessTest(unittest.TestCase):
    """A set of tests to ensure that the Publish-Subscribe
        server obeys the contract provided in the exercise
        """
    port = 8081
    publisher = PublishSubscribeResource()
    
    @classmethod
    def setUpClass(cls):
        #Start the server
        site = server.Site(cls.publisher)
        reactor.listenTCP(cls.port, site)
        Thread(target=reactor.run, args=(False,)).start()
    
    @classmethod  
    def tearDownClass(cls):
        # Stop the server
        reactor.callFromThread(reactor.stop)
        
    def tearDown(self):
        # After each individual test clear the server's data
        # structures to give test independence.
        CorrectnessTest.publisher._clear()
        
    def testSubscribe(self):
        # Test a simple subscribe.
        response = requests.post("http://localhost:%d/weather/bob" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        
    def testPostMessage(self):
        # Test a simple post of message to a topic.
        response = requests.post("http://localhost:%d/weather" % self.port, data='cloudy')
        self.assertEqual(response.status_code, 200)
        
    def testSubscribeAndPostMessage(self):
        # Test the non-error case of the basic sequence.
        response = requests.post("http://localhost:%d/weather/bob" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        response = requests.post("http://localhost:%d/weather" % self.port, data='cloudy')
        self.assertEqual(response.status_code, 200)
        
    def testSubscribeAndGetMessage(self):
        self.testSubscribeAndPostMessage()
        # Having subscribed and posted now ensure we get a positive response
        # code, and that we have the content we expect.
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.text, "cloudy")
        
    def testGetMessageTwice(self):
        self.testSubscribeAndGetMessage()
        # Attempting to get the message this time should return a 204.
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 204)
        
    def testGetMessageNotSubscribed(self):
        self.testPostMessage()
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 404)
       
    def testGetMessageMultipleSubscribers(self):
        # Both Bob and Alice subscribe to weather updates.
        self.subscribeAliceAndBobAndPost()
        # Both Bob and Alice should receive the new weather update.
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "cloudy")
        response = requests.get("http://localhost:%d/weather/alice" % self.port)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "cloudy")
        
    def testGetMessageForStillExistingTopicReturns204(self):
        # Both Bob and Alice subscribe to weather updates.
        self.subscribeAliceAndBobAndPost()
        # Both Bob and Alice should receive the new weather update.
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "cloudy")
        # Another attempt by Bob to get a weather update should be a 204,
        # (*you* have no more messages in this topic), not 404 (this topic
        # does not exist)
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 204)
        
    def testUnsubscribedWhenMessagePosted(self):
        # Bob subscribes to weather and a message is posted.
        self.testSubscribeAndPostMessage()
        # Alice now subscribes.
        response = requests.post("http://localhost:%d/weather/alice" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        # An attempt by Alice to get a weather update should be a 204, as
        # while she is subscribed, no message has been posted since.
        response = requests.get("http://localhost:%d/weather/alice" % self.port)
        self.assertEqual(response.status_code, 204)
        
    def testOnlyMessagePostedSinceSubscriptionReceived(self):
        # Bob subscribes to weather and a message is posted.
        self.testSubscribeAndPostMessage()
        # Alice now subscribes.
        response = requests.post("http://localhost:%d/weather/alice" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        # Post a new update to "weather". This is what Alice should receive if she
        # queries the weather.
        message = '...now it\'s sunny...oh no, wait, cloudy again!'
        response = requests.post("http://localhost:%d/weather" % self.port, data=message)
        self.assertEqual(response.status_code, 200)
        # An attempt by Alice to get a weather update should be a 204, as
        # while she is subscribed, no message has been posted since.
        response = requests.get("http://localhost:%d/weather/alice" % self.port)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, message)
        
    def testOldestPostedMessageShouldBeReceived(self):
        """What is the contract here? If Bob is subscribed to weather
            updates, and message A and B are posted, then Bob requests
            an update, should A be delivered first?"""
        pass
        
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
        
    
    ############################################################################
    # Helper functions
    ############################################################################
    
    def subscribeAliceAndBobAndPost(self):
        response = requests.post("http://localhost:%d/weather/bob" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        response = requests.post("http://localhost:%d/weather/alice" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        # Post a weather update.
        response = requests.post("http://localhost:%d/weather" % self.port, data='cloudy')
        self.assertEqual(response.status_code, 200)
             
if __name__ == '__main__':
    unittest.main()
        