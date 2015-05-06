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
    # When 
    topics = {}
    isLeaf = True
    def render_GET(self, request):
        # placeholder print
        print "got a GET......" 
        return "{0}".format(request.args.keys())
    def render_POST(self, request):
        # Child should be a topic name, in which case
        # we create a new entry.
        print "got a POST......"
        if len(request.postpath) != 1:
            raise ValueError( "Invalid num args!" )
        topic = request.postpath[0]
        print "topic is \"%s\"" % topic
        message = request.content.read()
        return "the message body was \"%s\"" % message
    def render_DELETE(self, request):
        pass
        
site = server.Site(Publisher())
port = 8081
reactor.listenTCP(8081, site)
print "starting....."
print "listening on %d" % port
reactor.run()
        
        