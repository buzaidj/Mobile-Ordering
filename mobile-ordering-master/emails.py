from imapclient import IMAPClient
import imapclient.exceptions
import json, time
from datetime import datetime
import email
from email import policy
from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
from email.mime.text import MIMEText

import sys
import os
import re

import pytz
from tzlocal import get_localzone
import phonenumbers
from escpos.printer import Usb, Dummy


class SendManager:
    def __init__(self, config_dict):
        SMTPserver = config_dict['smtp host name']
        port_num = int(config_dict['port number'])
        self.config_dict = config_dict

        self.sender = config_dict['outgoing username']
        self.text_subtype = 'plain'

        self.conn = SMTP(SMTPserver)
        self.conn.set_debuglevel(False)
        self.conn.login(config_dict['outgoing username'], config_dict['outgoing password'])

    def send_email(self, destination, subject, msg_content):
        msg = MIMEText(msg_content, self.text_subtype)
        msg['Subject'] = subject
        msg['From'] = self.sender

        try:
            self.conn.sendmail(self.sender, destination, msg.as_string())
        except Exception as e:
            print(e)
            return False
        finally:
            self.conn.quit()
            return True

class ReadEmail:
    def __init__(msgid, raw_email):
        email_message = email.message_from_bytes(raw_email[b'RFC822'], policy = policy.default)
        self.subject = email_message.get('Subject')
        self.body = str(email_message.get_body('text/plain'))
        self.body = self.body[self.body.find('{'): self.body.find('}') + 1]
        self.body = self.body.replace('\n', '')
        try:
            self.body_dict = json.loads(self.body)
        except:
            self.body_dict = {}

        try:
            dt_str = str(email_message.get('Date'))
            self.dt = datetime.strptime(dt_str, self.email_time_format).astimezone(self.tz)
            self.date = self.dt.strftime(self.date_format)
            self.time = self.dt.strftime(self.time_format)
        except:
            self.dt = datetime.now()
            self.date = self.dt.strftime(self.date_format)
            self.time = self.dt.strftime(self.time_format)


class ReadManager:
    def __init__(self, config_dict):
        self.conn = IMAPClient(host="imap.gmail.com")
        self.conn.login(config_dict['incoming username'], config_dict['incoming password'])
        self.conn.select_folder('INBOX')

    def check_emails(self, who_from):
        new_messages = self.conn.search([['FROM', who_from]])
        emails = []
        for msgid, raw_email in self.conn.fetch(new_messages, 'RFC822').items():
            emails.append(ReadEmail(msgid, raw_email))

        self.conn.delete_messages(new_messages)
        self.conn.expunge()
        self.conn.noop()

        return emails

    def logout(self):
        self.conn.logout()
