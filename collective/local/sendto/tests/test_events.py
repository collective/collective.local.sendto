# -*- coding: utf-8 -*-
from collective.local.sendto.testing import IntegrationTestCase
from collective.local.sendto.events import MailSentEvent


class TestEvents(IntegrationTestCase):
    """Test collective.local.sendto events."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        super(TestEvents, self).setUp()

    def test_mail_sent_event(self):
        event = MailSentEvent(subject=u"Mail subject",
                              body=u"Mail body text",
                              sender="lisasimpson",
                              recipients=['bartsimpson', 'homersimpson'])
        self.assertEqual(u"Mail subject", event.subject)
        self.assertEqual(u"Mail body text", event.body)
        self.assertEqual('lisasimpson', event.sender)
        self.assertIn('bartsimpson', event.recipients)
        self.assertIn('homersimpson', event.recipients)
        self.assertNotIn('lisasimpson', event.recipients)
