from twisted.trial import unittest
import requests
from publisher import Publisher
from twisted.web import server
from twisted.internet import reactor
from threading import Thread

class CorrectnessTest(unittest.TestCase):

    port = 8081
    publisher = Publisher()
    
    @classmethod
    def setUpClass(cls):
        print "I'm being called....."
        #Start the server
        site = server.Site(cls.publisher)
        #reactor.listenTCP(cls.port, site)
        reactor.listenTCP(8081, site)
        Thread(target=reactor.run, args=(False,)).start()
        print "listening on 8081......"
    
    @classmethod  
    def tearDownClass(cls):
        # Stop the server
        print "I'm here!!"
        reactor.callFromThread(reactor.stop)
        
    def tearDown(self):
        # After each individual test clear the server's data
        # structures to give test independence.
        CorrectnessTest.publisher._clear()
        
    def testSubscribe(self):
        response = requests.post("http://localhost:%d/weather/bob" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        
    #def testPostMessage(self):
    #   response = requests.post("http://localhost:%d/weather" % self.port, data='cloudy')
    #    self.assertEqual(response.status_code, 200)
        
#if __name__ == '__main__':
#    unittest.main()
        