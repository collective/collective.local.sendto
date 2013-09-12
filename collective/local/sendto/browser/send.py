# -*- coding: utf-8 -*-
import re

from zope.event import notify

from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from collective.local.sendto.events import MailSentEvent
from collective.local.sendto.utils import get_images_from_body, send_mail


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

        actor = portal_membership.getAuthenticatedMember()
        actor_fullname = actor.getProperty('fullname', actor.getId())
        actor_email = actor.getProperty('email', None)
        actor_signature = actor.getProperty('signature', '')

        if actor_email:
            mfrom = (actor_fullname, actor_email)
        else:
            mfrom = (context.email_from_name, context.email_from_address)

        template = getattr(context, 'collective_sendto_template')
        body = template(self, self.request,
                        email_message=email_body,
                        actor_fullname=actor_fullname,
                        actor_signature=actor_signature)
        body = re.sub(r'([^"])(http[s]?[^ <]*)', r'\1<a href="\2">\2</a>', body)


        mail_sent_event = MailSentEvent(subject=email_subject,
                                        body=unmodified_email_body,
                                        recipients=recipients)
        
        mail_sent = send_mail(subject=email_subject, 
                              body=body, mfrom=mfrom, 
                              mto=mto, images=images)

        if mail_sent:
            notify(mail_sent_event)
