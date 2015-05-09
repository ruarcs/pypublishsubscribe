import unittest
import requests
from pypublishsubscribe.publishsubscriberesource import PublishSubscribeResource
from twisted.web import server
from twisted.internet import reactor
from threading import Thread
from Queue import Queue

class BasePublishSubscribeTest(unittest.TestCase):
    """A skeleton for a test that allows requests to
        be sent to the server, and clears the server
        after each test, to allow test independence.
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
        BasePublishSubscribeTest.publisher._clear()
