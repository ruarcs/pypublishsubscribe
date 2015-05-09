import unittest
import requests
from pypublishsubscribe.publishsubscribeserver import PublishSubscribeServer
from twisted.web import server
from twisted.internet import reactor
from threading import Thread
from Queue import Queue

class PublishSubscribeTest(unittest.TestCase):
    """A set of tests for the server, including tests both
       for correctness and load. It clears the server data structures
       after each test, to allow test independence.
        """
    port_number = 0
    publisher = PublishSubscribeServer()

    @classmethod
    def setUpClass(cls):
        #Start the server
        site = server.Site(cls.publisher)
        port = reactor.listenTCP(0, site)
        # Allow OS to pick an available port.
        cls.port_number = port.getHost().port
        Thread(target=reactor.run, args=(False,)).start()

    @classmethod
    def tearDownClass(cls):
        # Stop the server
        reactor.callFromThread(reactor.stop)

    def tearDown(self):
        # After each individual test clear the server's data
        # structures to give test independence.
        PublishSubscribeTest.publisher._clear()

    ###########################################################
    # A set of simple correctness tests to check that the server
    # correctly adheres to the contract specified.
    ###########################################################

    def testSubscribe(self):
        # Test a simple subscribe.
        response = requests.post("http://localhost:%d/weather/bob" % self.port_number, data='')
        self.assertEqual(response.status_code, 200)

    def testPostMessage(self):
        # Test a simple post of message to a topic.
        response = requests.post("http://localhost:%d/weather" % self.port_number, data='cloudy')
        self.assertEqual(response.status_code, 200)

    def testSubscribeAndPostMessage(self):
        # Test the non-error case of the basic sequence.
        response = requests.post("http://localhost:%d/weather/bob" % self.port_number, data='')
        self.assertEqual(response.status_code, 200)
        response = requests.post("http://localhost:%d/weather" % self.port_number, data='cloudy')
        self.assertEqual(response.status_code, 200)

    def testSubscribeAndGetMessage(self):
        self.testSubscribeAndPostMessage()
        # Having subscribed and posted now ensure we get a positive response
        # code, and that we have the content we expect.
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.text, "cloudy")

    def testGetMessageTwice(self):
        self.testSubscribeAndGetMessage()
        # As only one message has been posted to this topic,
        # attempting to get a message a second time should return a 204.
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.status_code, 204)

    def testGetMessageNotSubscribed(self):
        self.testPostMessage()
        # A message has been posted, but Bob has not subscribed.
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.status_code, 404)

    def testGetMessageMultipleSubscribers(self):
        # Both Bob and Alice subscribe to weather updates.
        self.subscribeAliceAndBobAndPost()
        # Both Bob and Alice should receive the new weather update.
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "cloudy")
        # The message should still be available to Alice.
        response = requests.get("http://localhost:%d/weather/alice" % self.port_number)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "cloudy")

    def testGetMessageForStillExistingTopicReturns204(self):
        # Both Bob and Alice subscribe to weather updates.
        self.subscribeAliceAndBobAndPost()
        # Both Bob and Alice should receive the new weather update.
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "cloudy")
        # Another attempt by Bob to get a weather update should be a 204,
        # (you have no more messages in this topic), not 404 (this topic
        # does not exist).
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.status_code, 204)

    def testUnsubscribedWhenMessagePosted(self):
        # Bob subscribes to weather, and a message is posted.
        self.testSubscribeAndPostMessage()
        # Alice now subscribes.
        response = requests.post("http://localhost:%d/weather/alice" % self.port_number, data='')
        self.assertEqual(response.status_code, 200)
        # An attempt by Alice to get a weather update should be a 204, as
        # while she is subscribed, no message has been posted since.
        response = requests.get("http://localhost:%d/weather/alice" % self.port_number)
        self.assertEqual(response.status_code, 204)

    def testOnlyMessagePostedSinceSubscriptionReceived(self):
        # Bob subscribes to weather and a message is posted.
        self.testSubscribeAndPostMessage()
        # Alice now subscribes.
        response = requests.post("http://localhost:%d/weather/alice" % self.port_number, data='')
        self.assertEqual(response.status_code, 200)
        # Post a new update to "weather". This is what Alice should receive if she
        # queries the weather.
        message = '...now it\'s sunny...oh no, wait, cloudy again!'
        response = requests.post("http://localhost:%d/weather" % self.port_number, data=message)
        self.assertEqual(response.status_code, 200)
        # An attempt by Alice to get a weather update should get only
        # the messages that have been pushed since she subscribed.
        response = requests.get("http://localhost:%d/weather/alice" % self.port_number)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, message)
        # Another attempt by Alice to get a message should result in a 204,
        # as she has received all messages since her subscription.
        response = requests.get("http://localhost:%d/weather/alice" % self.port_number)
        self.assertEqual(response.status_code, 204)


    def testOldestPostedMessageShouldBeReceived(self):
        """Check that messages are received in a FIFO manner."""
        # Bob subscribes to weather and a message ("cloudy") is posted.
        self.testSubscribeAndPostMessage()
        # Now post a new update, before Bob has a chance to make a request.
        message = '...now it\'s sunny...oh no, wait, cloudy again!'
        response = requests.post("http://localhost:%d/weather" % self.port_number, data=message)
        # If Bob checks the "weather" topic now he should get the first
        # message posted, not the most recent one.
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.status_code, 200)
        # Check that it was the message originally posted that we received.
        self.assertEqual(response.text, "cloudy")

    def testUnsubscribeBeforeChecking(self):
        # Bob subscribes to weather and a message is posted.
        self.testSubscribeAndPostMessage()
        # Bob now unsubscribes before requesting the message
        response = requests.delete("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEquals(response.status_code, 200)
        # If Bob now tries to retrieve the message he should get a 404.
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.status_code, 404)

    def testResubscribe(self):
        # Bob subscribes to weather and a message is posted.
        self.testSubscribeAndPostMessage()
        # Bob now unsubscribes before requesting the message
        response = requests.delete("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEquals(response.status_code, 200)
        # Bob now resubscribes.
        response = requests.post("http://localhost:%d/weather/bob" % self.port_number, data='')
        self.assertEqual(response.status_code, 200)
        # If Bob now tries to retrieve the message he should get a 204,
        # indicating that there are no messages for him on this topic.
        # He should *not* get the message posted before he unsubscribed,
        # and he also should *not* get a 404, as this is a valid subscription.
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.status_code, 204)

    def testGetInvalidResourceGives404AndServerStaysUp(self):
        # Bob subscribes to weather and a message is posted.
        self.testSubscribeAndPostMessage()
        # Getting an invalid resource should give a 404.
        response = requests.get("http://localhost:%d/weather/bob/foo" % self.port_number)
        self.assertEqual(response.status_code, 404)
        # But the server should have handled this gracefully, and should
        # return correctly if Bob requests a message.
        response = requests.get("http://localhost:%d/weather/bob" % self.port_number)
        self.assertEqual(response.status_code, 200)

    def testDeleteInvalidResourceGives404AndServerStaysUp(self):
        response = requests.post("http://localhost:%d/weather/bob" % self.port_number, data='')
        self.assertEqual(response.status_code, 200)
        # Deleting an invalid resource should give a 404.
        response = requests.delete("http://localhost:%d/weather" % self.port_number)
        self.assertEqual(response.status_code, 404)
        # But the server should have handled this gracefully, and should
        # allow a new message to be posted to this topic.
        response = requests.post("http://localhost:%d/weather" % self.port_number, data='cloudy')
        self.assertEqual(response.status_code, 200)

    ###########################################################
    # A set of simple load tests to validate that the server
    # will stay up under load.
    ###########################################################

    def testSimpleLoadTestWithSubscription(self):
        """Simulate a single user sending many requests."""
        def sendRequestExpect200():
            response = requests.get("http://localhost:%d/weather/alice" % self.port_number)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, 'cloudy')
        # Subscribe Alice to weather updates so that messages
        # are persisted when posted.
        response = requests.post("http://localhost:%d/weather/alice" % self.port_number, data='')
        self.assertEqual(response.status_code, 200)
        # Check that server stays up after multiple requests.
        self.runMultipleRequests(100, sendRequestExpect200)

    def testLoadTestRequestsMultipleUsers(self):
        """Simulate multiple users making concurrent requests for messages."""
        user_list = ['alice', 'bob', 'charles']
        def sendRequestExpect200():
            for user in user_list:
                response = requests.get("http://localhost:%d/weather/%s" % (self.port_number, user))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.text, 'cloudy')
        # Subscribe all users to weather updates so that messages
        # are persisted when posted.
        for user in user_list:
            response = requests.post("http://localhost:%d/weather/%s" % (self.port_number, user), data='')
            self.assertEqual(response.status_code, 200)
        # Check that server stays up when subjected to requests from multiple users.
        self.runMultipleRequests(50, sendRequestExpect200)

    def testPostNewMessagesWithMultipleSubscribers(self):
        """Simulate multiple users making concurrent requests for messages,
            while new messages are being posted to this topic."""
        user_list = ['alice', 'bob', 'charles']
        def postMessageAndSendRequest():
            for user in user_list:
                response = requests.post("http://localhost:%d/weather" % self.port_number, data='sunny')
                self.assertEqual(response.status_code, 200)
                response = requests.get("http://localhost:%d/weather/%s" % (self.port_number, user))
                self.assertEqual(response.status_code, 200)
        # Subscribe all users to weather updates so that messages
        # are persisted when posted.
        for user in user_list:
            response = requests.post("http://localhost:%d/weather/%s" % (self.port_number, user), data='')
            self.assertEqual(response.status_code, 200)
        # Check that server stays up after multiple requests.
        self.runMultipleRequests(50, postMessageAndSendRequest)

    ############################################################################
    # Helper functions
    ############################################################################

    def runMultipleRequests(self, concurrency_level, action):
        for i in range(concurrency_level):
            # Post a series of weather updates for user to receive.
            response = requests.post("http://localhost:%d/weather" % self.port_number, data='cloudy')
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

    def subscribeAliceAndBobAndPost(self):
        response = requests.post("http://localhost:%d/weather/bob" % self.port_number, data='')
        self.assertEqual(response.status_code, 200)
        response = requests.post("http://localhost:%d/weather/alice" % self.port_number, data='')
        self.assertEqual(response.status_code, 200)
        # Post a weather update.
        response = requests.post("http://localhost:%d/weather" % self.port_number, data='cloudy')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
