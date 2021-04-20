#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Light e-mail utilities to send mail with Django.

'''

from django.core.mail import send_mail, EmailMultiAlternatives
from smtplib import SMTPConnectError
import socket

__all__ = ['send_mail', 'send_html_mail']

def send_mail(recipients, from_addr=None, subject=None, message=None):  
    """Sends a e-mail message to a list of recipients.
    
    Returns ``None`` to indicate success sending the message.
    """
    
    try:
        send_mail(subject, message, from_addr, recipients)
    except (SMTPConnectError, socket.error), e:
        # temporary problem connecting to the smtp server
        raise e
    
    return None

def send_html_mail(recipients, from_addr, 
    subject=None, message=None, content_type='text/html',
    html_message_class=EmailMultiAlternatives
    ):
    """Sends a HTML message using the ``EmailMultiAlternatives`` class."""
    email = html_message_class(subject, message, from_addr, recipients)
    email.attach_alternative(message, content_type)
    email.send()
    
    return None

