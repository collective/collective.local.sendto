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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from Products.ATContentTypes.interfaces.image import IATImage

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


def get_images_from_body(body, context):
    image_links = re.findall(r'<img[^>]*src="([^"]*)"[^>]*>', body)
    images = []

    resolver = context.unrestrictedTraverse('@@resolveuid_and_caption')
    resolver.resolve_uids = True
    def resolve_image(src):
        if 'resolveuid' in src:
            image_info = resolver.resolve_image(image_link)
            if image_info[0] is None:
                return None
            image_file = image_info[0]
        else:
            try:
                image_file = context.unrestrictedTraverse(src)
            except AttributeError:
                log.error("Couldn't retrieve %s", src)
                return None

        return image_file

    # img elements
    for image_link in list(set(image_links)):
        image_file = resolve_image(image_link)
        if not image_file:
            log.error("No image found for link: %s", image_link)
            continue

        if IATImage.providedBy(image_file):
            image_file = image_file.getFile()

        image_filename = image_file.filename
        images.append(image_file)
        body = body.replace(image_link, "cid:%s" % image_filename)

    # input images
    input_image_links = re.findall(r'<input[^>]*type="image"[^>]*src="([^"]*)"[^>]*>', body)
    for image_link in list(set(input_image_links)):
        image_file = resolve_image(image_link)
        image_filename = image_file.filename
        images.append(image_file)
        body = re.sub(
            r'<input([^>]*)type="image"([^>]*)src="' + image_link + r'"([^>]*)>',
            r'<img\1\2src="cid:' + image_filename + r'"\3>',
            body)

    return body, images


class Send(BrowserView):

    def send(self):
        context = self.context
        portal_membership = getToolByName(context, 'portal_membership')
        form = self.request.form
        email_body = form.get('email_body')

        email_body, images = get_images_from_body(email_body, context)

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

        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = email_subject
        msgRoot['From'] = mfrom
        msgRoot.attach(MIMEText(body, 'html', 'utf-8'))

        for image in images:
            msgImage = MIMEImage(image.data, image.get_content_type().split('/')[1])
            msgImage.add_header('Content-ID', image.filename)
            msgRoot.attach(msgImage)

        for recipient in mto:
            try:
                mailhost.send(
                    msgRoot,
                    mto = [recipient])
            except MailHostError, e:
                log.error("%s : %s", e, recipient)

