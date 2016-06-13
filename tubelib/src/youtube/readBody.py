from twisted.internet import protocol

# this is a backport from Twisted 14.0 .. because Twisted 12.x in the denzil oe doesnt support it

class _ReadBodyProtocol(protocol.Protocol):
    """
    Protocol that collects data sent to it.
        
    This is a helper for L{IResponse.deliverBody}, which collects the body and
    fires a deferred with it.
        
    @ivar deferred: See L{__init__}.
    @ivar status: See L{__init__}.
    @ivar message: See L{__init__}.

    @ivar dataBuffer: list of byte-strings received
    @type dataBuffer: L{list} of L{bytes}
    """
    
    def __init__(self, status, message, deferred):
        """
        @param status: Status of L{IResponse}
        @ivar status: L{int}
        
        @param message: Message of L{IResponse}
        @type message: L{bytes}

        @param deferred: deferred to fire when response is complete
        @type deferred: L{Deferred} firing with L{bytes}
        """
        self.deferred = deferred
        self.status = status
        self.message = message
        self.dataBuffer = []


    def dataReceived(self, data):
        """
        Accumulate some more bytes from the response.
        """
        self.dataBuffer.append(data)


    def connectionLost(self, reason):
        """
        Deliver the accumulated response bytes to the waiting L{Deferred}, if
        the response body has been completely received without error.
        """
        if reason.check(ResponseDone):
            self.deferred.callback(b''.join(self.dataBuffer))
        elif reason.check(PotentialDataLoss):
            self.deferred.errback(
                PartialDownloadError(self.status, self.message,
                                     b''.join(self.dataBuffer)))
        else:
            self.deferred.errback(reason)

def readBody(response):
    """
    Get the body of an L{IResponse} and return it as a byte string.

    This is a helper function for clients that don't want to incrementally
    receive the body of an HTTP response.

    @param response: The HTTP response for which the body will be read.
    @type response: L{IResponse} provider

    @return: A L{Deferred} which will fire with the body of the response.
    """
    d = defer.Deferred()
    response.deliverBody(_ReadBodyProtocol(response.code, response.phrase, d))
    return d
