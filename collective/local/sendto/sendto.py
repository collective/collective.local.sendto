# -*- coding: utf-8 -*-
import re

from AccessControl.ImplPython import rolesForPermissionOn
from zope.i18nmessageid import MessageFactory
from zope.component import getUtility
from zope.i18n import translate

from Products.Five.browser import BrowserView
from plone.stringinterp.adapters import _recursiveGetMembersFromIds
from Products.CMFCore.utils import getToolByName
from Products.MailHost.MailHost import formataddr, MailHostError
from Products.MailHost.interfaces import IMailHost

from collective.local.sendto import log, SendToMessageFactory as _
from collective.local.sendto.interfaces import ISendToAvailable

PMF = MessageFactory('plone')


class Expressions(BrowserView):

    def sendto_available(self):
        return ISendToAvailable.providedBy(self.context)


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

    def users_by_role(self):
        """a list of dictionnaries
            {'role': message,
             'users': list of users}
        """
        context = self.context
        portal = getToolByName(context, 'portal_url').getPortalObject()
        site_url = portal.absolute_url()

        roles = getToolByName(context, 'portal_properties').site_properties.sendToRecipientRoles
        roles = [r for r in roles if r in rolesForPermissionOn('View', self.context)]

        infos = []
        ismanager = self.ismanager()

        for role in roles:
            users = recursive_users_with_role(context, portal, role)
            if len(users) == 0:
                continue

            role_infos = {'role': PMF(role)}
            role_infos['users'] = []
            for user in users:
                user_id = user.getUserName()
                if ismanager:
                    home = "%s/prefs_user_details?userid=%s" % (site_url, user_id)
                else:
                    home = "%s/author/%s" % (site_url, user_id)

                user_infos = {'userid': user_id,
                              'fullname': user.getProperty('fullname') or user_id,
                              'home': home,
                              'email': user.getProperty('email'),
                              }
                role_infos['users'].append(user_infos)

            infos.append(role_infos)

        return infos


class Send(BrowserView):

    def send(self):
        context = self.context
        portal_membership = getToolByName(context, 'portal_membership')
        form = self.request.form
        email_body = form.get('email_body')
        email_subject = form.get('email_subject')

        roles = getToolByName(context, 'portal_properties').site_properties.sendToRecipientRoles

        principals = []
        for role in roles:
            selected_for_role = form.get(role, [])
            for principal in selected_for_role:
                if principal not in principals:
                    principals.append(principal)

        if not principals:
            return

        recipients = []
        for userid in principals:
            user = portal_membership.getMemberById(userid)
            if user is None:
                pass
            else:
                recipients.append(user)

        mto = [(recipient.getProperty('fullname', recipient.getId()),
                recipient.getProperty('email')) for recipient in
                recipients]
        mto = [formataddr(r) for r in mto if r[1] is not None]

        actor = portal_membership.getAuthenticatedMember()
        actor_fullname = actor.getProperty('fullname', actor.getId())
        actor_email = actor.getProperty('email', None)
        actor_signature = actor.getProperty('signature', '')

        if actor_email:
            mfrom = formataddr((actor_fullname, actor_email))
        else:
            mfrom = formataddr((context.email_from_name,
                                context.email_from_address))

        template = getattr(context, 'collective_sendto_template')
        body = template(self, self.request,
                        email_message=email_body,
                        actor_fullname=actor_fullname,
                        actor_signature=actor_signature)
        body = re.sub(r'([^"])(http[s]?[^ <]*)', r'\1<a href="\2">\2</a>', body)

        mailhost = getUtility(IMailHost)

        for recipient in mto:
            try:
                mailhost.send(
                    body,
                    mto = [recipient],
                    mfrom = mfrom,
                    subject = email_subject,
                    msg_type = 'text/html',
                    charset = 'utf-8')
            except MailHostError, e:
                log.error("%s : %s", e, recipient)

