from twisted.internet import reactor, protocol

class Publisher(protocol.Protocol):
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
    
    def dataReceived(self, data)
        