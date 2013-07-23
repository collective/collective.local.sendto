from zope.interface import implements

from collective.local.sendto.interfaces import IMailSentEvent


class MailSentEvent(object):
    """Event notified when a mail is sent"""
    implements(IMailSentEvent)
    subject = u''
    body = u''
    recipients = []

    def __init__(self, subject, body, recipients, **kwargs):
        self.subject = subject
        self.body = body
        self.recipients = recipients
        self.kwargs = kwargs
