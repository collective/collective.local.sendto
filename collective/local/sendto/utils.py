# -*- coding: utf-8 -*-
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import re

from zope.component import getUtility

from Products.MailHost.MailHost import MailHostError
from Products.MailHost.MailHost import formataddr
from Products.MailHost.interfaces import IMailHost
from Products.ATContentTypes.interfaces.image import IATImage

from collective.local.sendto import log


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

    return body, tuple(images)


def send_mail(subject=None, body=None, mfrom=None, mto=None, images=(),
              content_type='html'):
    mfrom = formataddr(mfrom)
    mto = [formataddr(r) for r in mto if r[1] is not None]
    mailhost = getUtility(IMailHost)

    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = subject
    msgRoot['From'] = mfrom
    msgRoot.attach(MIMEText(body, content_type, 'utf-8'))

    for image in images:
        msgImage = MIMEImage(image.data,
                             image.get_content_type().split('/')[1])
        msgImage.add_header('Content-ID', image.filename)
        msgRoot.attach(msgImage)

    mail_sent = False
    for recipient in mto:
        try:
            mailhost.send(
                msgRoot,
                mto = [recipient])
            mail_sent = True
        except MailHostError, e:
            log.error("%s - %s : %s", e, recipient)

    return mail_sent