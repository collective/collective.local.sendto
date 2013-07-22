# -*- coding: utf-8 -*-
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import re

from zope.component import getUtility
from zope.event import notify

from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.MailHost.MailHost import formataddr, MailHostError
from Products.MailHost.interfaces import IMailHost
from Products.ATContentTypes.interfaces.image import IATImage

from collective.local.sendto import log
from collective.local.sendto.events import MailSentEvent


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
        unmodified_email_body = form.get('email_body')

        email_body, images = get_images_from_body(unmodified_email_body, context)

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

        mail_sent_event = MailSentEvent(subject=email_subject,
                                        body=unmodified_email_body,
                                        sender=mfrom,
                                        recipients=recipients)
        mail_sent = False
        for recipient in mto:
            try:
                mailhost.send(
                    msgRoot,
                    mto = [recipient])
                mail_sent = True
            except MailHostError, e:
                log.error("%s : %s", e, recipient)

        if mail_sent:
            notify(mail_sent_event)
