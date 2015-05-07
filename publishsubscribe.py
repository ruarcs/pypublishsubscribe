import sys
from twisted.web import server, resource
from twisted.internet import reactor

class PublishSubscribeResource(resource.Resource):
    # This structure consists of
    # a dict of tuples. The key is the topic
    # name. The value is a tuple of a list
    # of strings (the current subscribers),
    # and list of tuples (the messages).
    # Each tuple takes the form: 
    # (message, [subscriber_name_1, subscriber_name_2, ...])
    # When a new message is published copy the *current* list
    # of subscribers into a new tuple, so that we have an *independent*
    # of subscribers.
    topics = {}
    isLeaf = True
    
    def render_GET(self, request):
        if len(request.postpath) != 2:
            raise ValueError( "Invalid resource!" )
        topic = request.postpath[0]
        username = request.postpath[1]
        if not topic in self.topics:
            request.setResponseCode(404)
            return ""
        messages = self.topics[topic][1]
        for index, message in enumerate(list(messages)):
            # Enumerate over *copy* to allow removal.
            if username in message[1]:
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
            if topic in self.topics:
                # If topic has been subscribed to then add a new entry,
                # copying the list of current subscribers.
                topic_entry = self.topics[topic]
                topic_entry[1].append((message, topic_entry[0][:]))
            return 200, "Message successfully posted."
        def new_subscription(topic, username):
            if topic in self.topics:
                self.topics[topic][0].append(username)
            else:
                self.topics[topic] = ([username],[])
            return 200, "Subscription successful."
        postpath_length = len(request.postpath)
        if postpath_length == 0 or postpath_length > 2:
            raise ValueError( "Invalid resource!" )
        elif postpath_length == 2:
            response_code, status_message \
            = new_subscription(request.postpath[0], request.postpath[1])
        else:
            response_code, status_message \
            = new_message(request.postpath[0], request.content.read())
        request.setResponseCode(response_code)
        return status_message           
            
    def render_DELETE(self, request):
        if len(request.postpath) != 2:
            raise ValueError( "Invalid resource!" )
        topic = request.postpath[0]
        username = request.postpath[1]
        if not topic in self.topics or not username in self.topics[topic][0]:
            request.setResponseCode(404)
            return ""
        self.topics[topic][0].remove(username)
        if not self.topics[topic][0]:
            # If there are no more subscribers to this topic
            # then remove it.
            self.topics.remove(topic)
        else:
            # There are still subscribers. However we must
            # remove this user from any messages they are currently
            # subscribed to, otherwise this message will never
            # be deleted, and effectively leaks memory.
            pass
        request.setResponseCode(200)
        return "Successfully unsubscribed."
        
    def _clear(self):
        # Allow to fully clear the data structure.
        self.topics.clear()
       
def main():
    # Simple main method to allow the server to run, binding
    # to the specified port.
    if len(sys.argv) != 2:
        raise ValueError("Please provide a port number to listen on.")
    site = server.Site(PublishSubscribeResource())
    try:
        port = int( sys.argv[1])
    except:
        raise ValueError( "The port number must be a valid integer." )
    reactor.listenTCP(port, site)
    print "Starting server. Listening on %d." % port
    reactor.run()
    
if __name__ == '__main__':
    main()
        
        