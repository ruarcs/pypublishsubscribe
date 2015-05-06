from twisted.web import server, resource
from twisted.internet import reactor

class Publisher(resource.Resource):
    # This structure consists of
    # a dict of tuples. The key is the topic
    # name. The value is a tuple of a list
    # of strings (the current subscribers),
    # and list of tuples (the messages).
    # Each tuple takes the form: 
    # (message, [subscriber_name_1, subscriber_name_2, ...])
    # When a new message is published copy (b = a[:] or b = list(a))
    # the *current* list
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
        for message in messages:
            if username in message[1]:
                request.setResponseCode(200)
                return message[0]
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
        pass
        
site = server.Site(Publisher())
port = 8081
reactor.listenTCP(8081, site)
print "starting....."
print "listening on %d" % port
reactor.run()
        
        