from imapclient import IMAPClient
import imapclient.exceptions
import json, time
from datetime import datetime, date, timedelta, timezone
import queue
import email
from email import policy
from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
from email.mime.text import MIMEText
import json

import emails

class ConfigRead:
    config_filenames = ['client_secret', 'read_email_info', 'send_email_info', 'gsheets_info', 'printer_config']
    params = ['timestamp', 'name', 'number', 'order', 'notes', 'email', 'pickup_time', 'option']
    day_params =  ['order', 'notes', 'option']
    non_day_params = list(set(params) - set(day_params))

    """
    decodes json and sets filename accordingly
    """
    def decode_json(self, filename):
        filename = filename.replace('.json', '')
        try:
            with open(filename + '.json') as file:
                if filename in self.config_filenames:
                    self.config_dict[filename] = json.load(file)
                    return True
                else:
                    return False
        except json.JSONDecodeError as e:
            try:
                self.send_error_email(str(e), filename)
            except KeyError:
                print(str(e))


    def __init__(self):
        self.config_dict = {}
        for filename in self.config_filenames:
            self.decode_json(filename)
        self.destination = self.config_dict['send_email_info']['send status emails to']
        self.send_confirmation_email(str(self.config_filenames))

    """
    updates configs from a json_string
    """
    def update_configs(self, filename, json_string):
        filename = filename.replace('.json', '')
        if not filename in self.config_filenames:
            self.send_error_email('filename not in config_filenames', filename)
        else:
            try:
                self.config_dict[filename] = json.loads(json_string)
                with open(filename + '.json', 'w') as file:
                    file.write(json_string)
                self.send_confirmation_email(filename)
                return True
            except json.JSONDecodeError as e:
                try:
                    send_email_info = self.config_dict["send_email_info"]
                    self.send_error_email(str(e), filename)
                except KeyError:
                    print(str(e))


    def send_error_email(self, error, filename):
        send_client = emails.SendManager(self.config_dict['send_email_info'])
        text = 'There was an error setting up config filename.\nError ' + str(error) + '.\nFilename: ' + str(filename)
        send_client.send_email(destination = self.destination, subject = 'Error', msg_content = text)

    def send_confirmation_email(self, filename):
        send_client = emails.SendManager(self.config_dict['send_email_info'])
        text = str(filename) + ' initalized succesfully'
        send_client.send_email(destination = self.destination, subject = 'Success', msg_content = text)
