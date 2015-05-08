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
        """Simulate a single user sending many requests."""
        def sendRequestExpect200():
            response = requests.get("http://localhost:%d/weather/alice" % self.port)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, 'cloudy')
        # Subscribe Alice to weather updates so that messages
        # are persisted when posted.
        response = requests.post("http://localhost:%d/weather/alice" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        # Check that server stays up after multiple requests.
        self.run_test(100, sendRequestExpect200)

    def testLoadTestRequestsMultipleUsers(self):
        """Simulate multiple users making concurrent requests for messages."""
        user_list = ['alice', 'bob', 'charles']
        def sendRequestExpect200():
            for user in user_list:
                response = requests.get("http://localhost:%d/weather/%s" % (self.port, user))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.text, 'cloudy')
        # Subscribe all users to weather updates so that messages
        # are persisted when posted.
        for user in user_list:
            response = requests.post("http://localhost:%d/weather/%s" % (self.port, user), data='')
            self.assertEqual(response.status_code, 200)
        # Check that server stays up when subjected to requests from multiple users.
        self.run_test(50, sendRequestExpect200)

    def testPostNewMessagesWithMultipleSubscribers(self):
        """Simulate multiple users making concurrent requests for messages,
            while new messages are being posted to this topic."""
        user_list = ['alice', 'bob', 'charles']
        def postMessageAndSendRequest():
            for user in user_list:
                response = requests.post("http://localhost:%d/weather" % self.port, data='sunny')
                self.assertEqual(response.status_code, 200)
                response = requests.get("http://localhost:%d/weather/%s" % (self.port, user))
                self.assertEqual(response.status_code, 200)
        # Subscribe all users to weather updates so that messages
        # are persisted when posted.
        for user in user_list:
            response = requests.post("http://localhost:%d/weather/%s" % (self.port, user), data='')
            self.assertEqual(response.status_code, 200)
        # Check that server stays up after multiple requests.
        self.run_test(50, postMessageAndSendRequest)

    ############################################################################
    # Helper functions
    ############################################################################

    def run_test(self, concurrency_level, action):
        for i in range(concurrency_level):
            # Post a series of weather updates for user to receive.
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
