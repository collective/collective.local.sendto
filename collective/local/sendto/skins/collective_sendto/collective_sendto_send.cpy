## Controller Python Script "eprivr_mailing_list_send"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=email_subject, email_body, Editors=[], Reviewers=[], Readers=[], Members=[]
##title=Edit group members
##
from collective.local.sendto import SendToMessageFactory as _

context.restrictedTraverse('@@collective-sendto-send')()

context.plone_utils.addPortalMessage(_(u"Message sent."))
return state
