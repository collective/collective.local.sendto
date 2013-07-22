from zope.interface import Interface


class ISendToAvailable(Interface):
    """ Marker interface for contents that have send to feature """


class IMailSentEvent(Interface):
    pass
