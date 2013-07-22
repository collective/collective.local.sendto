# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.local.sendto.testing import IntegrationTestCase
from plone import api


class TestInstall(IntegrationTestCase):
    """Test installation of collective.local.sendto into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if collective.local.sendto is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.isProductInstalled('collective.local.sendto'))

    def test_uninstall(self):
        """Test if collective.local.sendto is cleanly uninstalled."""
        self.installer.uninstallProducts(['collective.local.sendto'])
        self.assertFalse(self.installer.isProductInstalled('collective.local.sendto'))
