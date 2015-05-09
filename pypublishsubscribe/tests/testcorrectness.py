import unittest
import requests
from basepublishsubscribetest import BasePublishSubscribeTest

class CorrectnessTest(BasePublishSubscribeTest):
    """A set of tests to ensure that the Publish-Subscribe
        server obeys the contract provided in the exercise.
        """
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
        # As only one message has been posted to this topic,
        # attempting to get a message this time should return a 204.
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 204)

    def testGetMessageNotSubscribed(self):
        self.testPostMessage()
        # A message has been posted, but Bob has not subscribed.
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
        # does not exist).
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 204)

    def testUnsubscribedWhenMessagePosted(self):
        # Bob subscribes to weather, and a message is posted.
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
        # An attempt by Alice to get a weather update should get only
        # the messages that have been pushed since she subscribed.
        response = requests.get("http://localhost:%d/weather/alice" % self.port)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, message)
        # Another attempt by Alice to get a message should result in a 204,
        # as she has received all messages since her subscription.
        response = requests.get("http://localhost:%d/weather/alice" % self.port)
        self.assertEqual(response.status_code, 204)


    def testOldestPostedMessageShouldBeReceived(self):
        """Check that messages are received in a FIFO manner."""
        # Bob subscribes to weather and a message is posted.
        self.testSubscribeAndPostMessage()
        message = '...now it\'s sunny...oh no, wait, cloudy again!'
        response = requests.post("http://localhost:%d/weather" % self.port, data=message)
        # If Bob checks the "weather" topic now he should get the first
        # message posted, not the most recent one.
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "cloudy")

    def testUnsubscribeBeforeChecking(self):
        # Bob subscribes to weather and a message is posted.
        self.testSubscribeAndPostMessage()
        # Bob now unsubscribes before requesting the message
        response = requests.delete("http://localhost:%d/weather/bob" % self.port)
        self.assertEquals(response.status_code, 200)
        # If Bob now tries to retrieve the message he should get a 404.
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 404)

    def testResubscribe(self):
        # Bob subscribes to weather and a message is posted.
        self.testSubscribeAndPostMessage()
        # Bob now unsubscribes before requesting the message
        response = requests.delete("http://localhost:%d/weather/bob" % self.port)
        self.assertEquals(response.status_code, 200)
        # Bob now resubscribes.
        response = requests.post("http://localhost:%d/weather/bob" % self.port, data='')
        self.assertEqual(response.status_code, 200)
        # If Bob now tries to retrieve the message he should get a 204,
        # indicating that there are no messages for him on this topic.
        # He should *not* get the message posted before he unsubscribed,
        # and he also should *not* get a 404, as this is a valid subscription.
        response = requests.get("http://localhost:%d/weather/bob" % self.port)
        self.assertEqual(response.status_code, 204)


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
