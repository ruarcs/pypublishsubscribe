import sys
from twisted.web import server, resource
from twisted.internet import reactor

class PublishSubscribeServer(resource.Resource):
    """A simple Publish-Subscribe server, allowing
        users to subscribe to messages on specific
        topics."""

    # The backing data structure here consists of
    # a dict of tuples. The key is the topic
    # name. The value is a tuple of a list
    # of strings (the current subscribers),
    # and list of tuples (the messages).
    # Each message tuple takes the form:
    # (message, [subscriber_name_1, subscriber_name_2, ...])
    # When a new message is published we copy the current list
    # of subscribers into a new tuple.
    topics = {}
    isLeaf = True


    def render_GET(self, request):
        """Handle a GET, which is a request by a user
            for any outstanding messages. A valid request
            will return a 200, and an invalid request will
            return a 404."""
        if len(request.postpath) != 2:
            # The only valid target for a GET
            # is /<topic>/<username>
            request.setResponseCode(404)
            return ""
        topic = request.postpath[0]
        username = request.postpath[1]
        if not topic in self.topics:
            # If a valid subscription doesn't exist
            # then return a 404.
            request.setResponseCode(404)
            return ""
        messages = self.topics[topic][1]
        # Check for any messages this user should be
        # returned. Send the oldest message first.
        for index, message in enumerate(list(messages)):
            # Enumerate over *copy* to allow removal.
            subscriber_list = message[1]
            if username in subscriber_list:
                # Not the message content to return.
                the_message = message[0]
                # Remove from *original* using index.
                messages[index][1].remove(username)
                if not messages[index][1]:
                    # If all users have received then
                    # delete the message, *from original list*.
                    del messages[index]
                request.setResponseCode(200)
                return the_message
        request.setResponseCode(204)
        return ""


    def render_POST(self, request):
        def new_message(topic, message):
            """Post a new message to a topic."""
            if topic in self.topics:
                # If topic has been subscribed to then add a new entry,
                # copying the list of current subscribers.
                topic_entry = self.topics[topic]
                topic_entry[1].append((message, topic_entry[0][:]))
            return 200, ""
        def new_subscription(topic, username):
            """Subscribe a user to a topic."""
            if topic in self.topics:
                # If the topic already exists then simply
                # add the user to the list of subscribers.
                self.topics[topic][0].append(username)
            else:
                # If the topic doesn't exist then add it,
                # and set the list of subscribers as the list
                # containing just this user, with messages
                # as an empty list.
                self.topics[topic] = ([username],[])
            return 200, ""
        postpath_length = len(request.postpath)
        if postpath_length == 1:
            response_code, status_message \
            = new_message(request.postpath[0], request.content.read())
        elif postpath_length == 2:
            response_code, status_message \
            = new_subscription(request.postpath[0], request.postpath[1])
        else:
            # The only valid targets are
            # /<topic> and /<topic>/<username>
            request.setResponseCode(404)
            return ""
        request.setResponseCode(response_code)
        return status_message


    def render_DELETE(self, request):
        if len(request.postpath) != 2:
            request.setResponseCode(404)
            return ""
        topic = request.postpath[0]
        username = request.postpath[1]
        if not topic in self.topics or not username in self.topics[topic][0]:
            # If this isn't a valid topic, or if user is not subscribed.
            request.setResponseCode(404)
            return ""
        # Remove the user from the list of subscribers
        # to this topic.
        self.topics[topic][0].remove(username)
        if not self.topics[topic][0]:
            # If there are no more subscribers to this topic
            # then remove it.
            del self.topics[topic]
        else:
            # There are still subscribers. However we must
            # remove this user from any messages they are currently
            # subscribed to on this topic, otherwise this message will never
            # be deleted, and effectively leaks memory.
            messages = self.topics[topic][1]
            for index, message in enumerate(list(messages)):
            # Enumerate over *copy* to allow removal.
                if username in message[1]:
                    # Remove from *original* using index.
                    messages[index][1].remove(username)
                    if not messages[index][1]:
                        # If all users have received then
                        # delete the message, *from original list*.
                        del messages[index]
        request.setResponseCode(200)
        return ""


    def _clear(self):
        # Allow to fully clear the data structure.
        # For use in unit testing.
        self.topics.clear()

def main():
    # Simple main method to allow the server to run, binding
    # to the specified port. Takes one arg, which is the port number.
    if len(sys.argv) != 2:
        raise ValueError("Please provide a port number to listen on.")
    site = server.Site(PublishSubscribeServer())
    try:
        port = int( sys.argv[1])
    except:
        raise ValueError( "The port number must be a valid integer." )
    reactor.listenTCP(port, site)
    print "Starting server. Listening on %d...." % port
    reactor.run()

if __name__ == "__main__":
    main()
