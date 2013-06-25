from AccessControl.ImplPython import rolesForPermissionOn
from zope.i18n import translate
from zope.i18nmessageid.message import MessageFactory

from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from plone.stringinterp.adapters import _recursiveGetMembersFromIds
from Products.statusmessages.interfaces import IStatusMessage

from collective.local.sendto.interfaces import ISendToAvailable
from collective.local.sendto import SendToMessageFactory as _

PMF = MessageFactory('plone')


def recursive_users_with_role(content, portal, role):
    # union with set of ids of members with the local role
    users_with_role = set(content.users_with_local_role(role))
    role_manager = portal.acl_users.portal_role_manager
    users_with_role |= set([p[0] for p in role_manager.listAssignedPrincipals(role)])
    return _recursiveGetMembersFromIds(portal, users_with_role)


class View(BrowserView):

    def ismanager(self):
        context = self.context
        return getToolByName(context, 'portal_membership').checkPermission('Manage portal', context)

    def default_subject(self):
        site_title = getToolByName(self.context, 'portal_url').getPortalObject().Title()
        context_title = self.context.Title()
        return "[%s] %s" % (site_title, context_title)

    def default_body(self):
        context_url = self.context.absolute_url()
        ptool = getToolByName(self.context, 'portal_properties').site_properties
        if self.context.portal_type in ptool.typesUseViewActionInListings:
            context_url += '/view'
        return """
            <p></p>
            <p>%s</p>""" % translate(_('mailing_body2',
                                           default="writing from ${context_url}",
                                           mapping={'context_url': context_url}),
                                         context=self.request)

    def _recipient_roles(self):
        roles = getToolByName(self.context, 'portal_properties').site_properties.sendToRecipientRoles
        roles = [r for r in roles if r in rolesForPermissionOn('View', self.context)]
        return roles

    def users_by_role(self):
        """a list of dictionnaries
            {'role': message,
             'users': list of users}
        """
        context = self.context
        portal = getToolByName(context, 'portal_url').getPortalObject()
        site_url = portal.absolute_url()

        infos = []
        roles = self._recipient_roles()

        for role in roles:
            users = recursive_users_with_role(context, portal, role)
            if len(users) == 0:
                continue

            role_infos = {'role': PMF(role)}
            role_infos['users'] = []
            for user in users:
                user_id = user.getUserName()
                home = "%s/author/%s" % (site_url, user_id)

                user_infos = {'userid': user_id,
                              'fullname': user.getProperty('fullname') or user_id,
                              'home': home,
                              'email': user.getProperty('email'),
                              }
                role_infos['users'].append(user_infos)

            infos.append(role_infos)

        return infos

    def __call__(self):
        context, request = self.context, self.request
        self.errors = {}

        if self.request.get('form.submitted', False):
            for role in self._recipient_roles():
                if self.request.get(role, None):
                    break
            else:
                self.errors['receipt'] = _(u'Please select at least one receipt')

            subject = context.REQUEST.get('email_subject', None)
            body = context.REQUEST.get('email_body', None)

            if not subject:
                self.errors['email_subject'] = _(u'Please fill the e-mail subject')

            if not body:
                self.errors['email_body'] = _(u'Please fill the e-mail body')

            if len(self.errors) > 0:
                IStatusMessage(request).add(PMF(u'Please correct the indicated errors.'), 'error')
            else:
                context.restrictedTraverse('@@collective-sendto-send')()
                IStatusMessage(request).add(_(u"Message sent."))
                request.response.redirect("%s/view" % context.absolute_url())
                return ""

        return super(View, self).__call__()


class Expressions(BrowserView):

    def sendto_available(self):
        return ISendToAvailable.providedBy(self.context)
