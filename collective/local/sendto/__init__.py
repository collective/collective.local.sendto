# -*- extra stuff goes here -*-
import logging
log = logging.getLogger('collective.local.sendto')

from AccessControl import allow_module
from zope.i18nmessageid import MessageFactory
from Products.PythonScripts.Utility import allow_module


SendToMessageFactory = MessageFactory('collective.local.sendto')

allow_module('collective.local.sendto.SendToMessageFactory')


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
