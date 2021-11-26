import config
import gsheets
import printing
import emails

import time
from datetime import datetime, date
import phonenumbers


class Main:
    def __init__(self, dummy):

        self.config = config.ConfigRead()
        self.sheets = gsheets.GSheets(self.config)
        self.cleared = False

        if dummy:
            self.printer = DummyPrinter()
        else:
            self.printer = UsbPrinter()

    def run(self):
        while True:
            orders = self.sheets.refresh_sheets(self.config)
            try:
                for order_dict in orders:
                    order = Order(order_dict)
                if not self.cleared and datetime.now().hour == 2: # resets set by removing old entrie at 3 am
                    self.sheets.clear_sheets()
                    self.cleared = True

                if datetime.now().hour in [22, 23, 0, 1, 2, 3, 4, 5, 6, 7]:
                    time.sleep(1800)
                else:
                    time.sleep(30)
            except Exception as e:
                print(e)
                SendManager()
                time.sleep(30)


"""
Class to represent an order


ALL ORDERS HAVE:
:param order_type: str
:param order_number: int
:param dt: dt
:param date: str
:param time: str

WORKING ORDERS HAVE
:param order_dict: dict
:param name: str
:param number: str
:param formatted_number: str
:param order: str
:param notes: str
:param pickup_time_dt: dt
:param pickup_time: str

"""
class Order:
    READ_order_datetime_format = '%-m/%d/%Y %H:%M:%S'
    READ_pickup_time_format = '%-I:%M%S %p'

    WRITE_order_date_format = "%b %-d"
    WRITE_order_time_format = "%-I:%M:%S %p"
    WRITE_pickup_time_format = "%-I:%M %p"


    def __init__(self, order_dict):
        self.order_dict = order_dict
        self.name = order_dict.pop('name')
        self.number = order_dict.pop('number')
        self.email = order_dict.pop('email')

        try:
            self.formatted_number = phonenumbers.format_number(phonenumbers.parse(self.number, 'US'), phonenumbers.PhoneNumberFormat.NATIONAL)
        except:
            self.formatted_number = self.number

        self.order_type = order_dict.pop('order_type')
        self.order_number = order_dict.pop('order_number')

        self.order = order_dict.pop('order')
        option = order.dict.pop('option')
        if option != '':
            self.order += '\n' + option
        self.notes = order_dict.pop('notes')

        try:
            self.dt = datetime.strptime(order_dict.pop('timestamp'), self.READ_order_datetime_format)
            self.date = self.dt.strftime(self.WRITE_order_date_format)
            self.time = self.dt.strftime(self.WRITE_order_time_format)
        except:
            self.dt = datetime.now()
            self.date = self.dt.strftime(self.WRITE_order_date_format)
            self.time = self.dt.strftime(self.WRITE_order_time_format)

        try:
            self.pickup_time_dt = datetime.strptime(order_dict.pop('pickup_time'), self.READ_pickup_time_format)
            self.pickup_time = self.pickup_time_dt.strftime(self.WRITE_pickup_time_format)
        except:
            self.pickup_time = order_dict.pop('pickup_time')

    def send_confirmation_email(self, config):
        organization_name = config.config_dict['send_email_info']['organization name']
        send_client = emails.SendManager(config.config_dict['send_email_info'])
        text = 'Hi ' + self.name + '.\n\n'
        text += 'Your ' + self.order_type.lower() + ' of ' + self.order + ' has printed succesfully. '
        text += 'It will be ready at ' + self.pickup_time + '.'
        try:
            send_client.send_email(destination = self.email, subject = organization_name + ' - Order Confirmation', msg_content = text)
        except:
            print('Email not sent')
