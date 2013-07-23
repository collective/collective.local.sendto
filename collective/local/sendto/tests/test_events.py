# -*- coding: utf-8 -*-
from plone import api

from collective.local.sendto.testing import IntegrationTestCase
from collective.local.sendto.events import MailSentEvent


class TestEvents(IntegrationTestCase):
    """Test collective.local.sendto events."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        super(TestEvents, self).setUp()

    def test_mail_sent_event(self):
        # TODO: test that the event is launched with plone.event
        bart = api.user.get('bart')
        homer = api.user.get('homer')
        event = MailSentEvent(subject=u"Mail subject",
                              body=u"Mail body text",
                              recipients=[bart, homer])
        self.assertEqual(u"Mail subject", event.subject)
        self.assertEqual(u"Mail body text", event.body)
        self.assertIn(bart, event.recipients)
        self.assertIn(homer, event.recipients)
