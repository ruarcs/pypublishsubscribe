import unittest
import requests
from publishsubscribe import PublishSubscribeResource
from twisted.web import server
from twisted.internet import reactor
from threading import Thread

class CorrectnessTest(unittest.TestCase):

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
        
    def testUnsubscribedUserGets404(self):
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
    
    ############################################################################
    # Helper functions
    ############################################################################
    
    def subscribeAliceAndBobAndPost(self):
        response = requests.post("http://localhost:%d/weather/bob" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        # Post a weather update.
        response = requests.post("http://localhost:%d/weather" % self.port, data='cloudy')
        self.assertEqual(response.status_code, 200)
        # A "weather" update does exist, but Alice had not subscribed at the time.
        response = requests.get("http://localhost:%d/weather/alice" % self.port)
        self.assertEqual(response.status_code, 404)
             
if __name__ == '__main__':
    unittest.main()
        