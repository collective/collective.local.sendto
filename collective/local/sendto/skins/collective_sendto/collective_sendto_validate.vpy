## Controller Validator "eprivr_mailing_list_validate"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=
##
from Products.CMFPlone import PloneMessageFactory as PMF
from collective.local.sendto import SendToMessageFactory as _

for role in context.portal_properties.site_properties.sendToRecipientRoles:
    if context.REQUEST.get(role, None):
        break
else:
    state.setError('receipt', _(u'Please select at least one receipt'), new_status='failure')

subject = context.REQUEST.get('email_subject', None)
body = context.REQUEST.get('email_body', None)

if not subject:
    state.setError('email_subject', _(u'Please fill the e-mail subject'), new_status='failure')

if not body:
    state.setError('email_body', _(u'Please fill the e-mail body'), new_status='failure')

if state.getErrors():
   state.setStatus('failure')
   context.plone_utils.addPortalMessage(PMF(u'Please correct the indicated errors.'), 'error')

return state
