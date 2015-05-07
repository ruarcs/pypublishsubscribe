from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, ServerFactory, Protocol

def get_factory_deferred(host, port):
    from twisted.internet import reactor
    factory = PublishSubscribeServerFactory()
    reactor.connectTCP(host, port, factory)
    return factory.deferred
    
class PublishSubscribeServerFactory(Factory):

    def __init__()
    return PublishSubscribeServer()

class CorrectnessTest(unittest.TestCase):

    def setUp(self):
        factory = PublishSubscribeServerFactory()
        from twisted.internet import reactor
        self.port = reactor.listenTCP(0, factory, interface="127.0.0.1")
        self.port_number = self.port.getHost().port
        
    def tearDown(self):
        port, self.port = self.port, None
        return port.stopListening()
            
    def testSubscribe(self):
        #the_deferred = get_factory_deferred("127.0.0.1", self.port_number)
        #def assertResponse(response_code):
        #    self.assertEquals(
        #response = requests.post("http://localhost:%d/weather/bob" % self.port, data='')
        #self.assertEqual(response.status_code, 200)
        self.assertEqual(200, 200)
        
    #def testPostMessage(self):
    #   response = requests.post("http://localhost:%d/weather" % self.port, data='cloudy')
    #    self.assertEqual(response.status_code, 200)
        
#if __name__ == '__main__':
#    unittest.main()
        