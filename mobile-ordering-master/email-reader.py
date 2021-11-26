import config
from printing import *
import emails

import time
from datetime import datetime, date
import phonenumbers

from escpos.printer import Usb, Dummy

import queue
import email

import config
import emails

import pygsheets

import time

class GSheet:
    def __init__(self, name, format, sheet):
        self.name = name
        self.format = format
        self.index_cell = sheet.cell(format['index'] + '1')
        self.index = int(self.index_cell.value)
        self.sheet = sheet

    def update_index(self):
        self.index_cell.value = self.index

class GSheets:
    def __init__(self, config):
        done = False
        while not done:
            try:
                print('Beginning Initalization')
                self.client = pygsheets.authorize(service_file='client_secret.json')
                time.sleep(1)
                self.sheets = []
                for name, params in config.config_dict['gsheets_info'].items():
                    sheet_name = params['spreadsheet_name']
                    format = params['format']
                    sh = self.client.open(sheet_name).sheet1
                    time.sleep(2)
                    gsheet = GSheet(name, format, sh)
                    time.sleep(1)
                    self.sheets.append(gsheet)
                done = True

                print("INITALIZED")
            except Exception as e:
                email_error = emails.SendManager(config.config_dict['send_email_info'])
                email_error.send_email(config.config_dict['send_email_info']['send status emails to'], subject = 'Error in initializing sheet', msg_content = str(e))
                time.sleep(30)

    # Poorly written and multiple nested try's and excepts. This was done by a much younger self!
    def refresh_sheets(self, config, printer):
        orders = []
        r = None
        while r == None:
            try:
                for gsheet in self.sheets:
                    gsheet.sheet.refresh()
                    time.sleep(5)
                    format = gsheet.format
                    while gsheet.sheet.cell('A' + str(gsheet.index)).value != '':
                        time.sleep(2)
                        order_dict =  {}
                        s_index = str(gsheet.index)
                        f = True
                        while f:
                            try:
                                if 'day' in gsheet.format:
                                    day = gsheet.sheet.cell(format['day'] + s_index).value.lower()
                                    for x in config.day_params:
                                        order_dict[x] = gsheet.sheet.cell(format[day + '_' + x] + s_index).value
                                        time.sleep(2)
                                    for x in config.non_day_params:
                                        order_dict[x] = gsheet.sheet.cell(format[x] + s_index).value
                                        time.sleep(2)
                                else:
                                    for x in config.params:
                                        order_dict[x] = gsheet.sheet.cell(format[x] + s_index).value
                                        time.sleep(2)
                                order_dict['order_type'] = gsheet.name.capitalize() + ' Order'
                                order_dict['order_number'] = gsheet.index % 100
                                orders.append(order_dict)

                                order = Order(order_dict)
                                printer.print_ticket(order)
                                order.send_confirmation_email(config)

                                f = False
                            except Exception as e:
                                try:
                                    print('ERROR')
                                    email_error = emails.SendManager(config.config_dict['send_email_info'])
                                    email_error.send_email(config.config_dict['send_email_info']['send status emails to'], subject = 'Error in getting sheet cells', msg_content = str(e))
                                    time.sleep(5)
                                except:
                                    time.sleep(5)


                        time.sleep(1)
                        print('Reading')
                        gsheet.index += 1

                    gsheet.update_index()
                r = orders
            except Exception as e:
                print(e)
                try:
                    email_error = emails.SendManager(config.config_dict['send_email_info'])
                    email_error.send_email(config.config_dict['send_email_info']['send status emails to'], subject = 'Error in refreshing sheet', msg_content = str(e))
                    time.sleep(30)
                except:
                    time.sleep(10)
        return orders

class Main:
    def __init__(self, dummy):
        self.reinitalize_at = [15, 2]
        self.config = config.ConfigRead()
        y = True
        while y:
            try:
                self.sheets = GSheets(self.config)
                y = False
            except Exception as e:
                print(e)
                time.sleep(30)
        self.cleared = False

        if dummy:
            self.printer = DummyPrinter()
        else:
            self.printer = UsbPrinter(self.config)

    def run(self):
        while True:
            if not self.cleared and datetime.now().hour in self.reinitalize_at: # reinitalizes api because had problems where program would go down after a while
                y = True
                while y:
                    try:
                        self.sheets = GSheets(self.config)
                        print('reinit')
                        y = False
                    except:
                        time.sleep(30)
                self.cleared = True
            if datetime.now().hour in [3, 16]:
                self.cleared = False
            else:
                time.sleep(1)

            self.sheets.refresh_sheets(self.config, self.printer) # prints as orders come in. A newer version uses yield


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
        option = order_dict.pop('option')
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
            self.pickup_time_dt = datetime.strptime(order_dict.get('pickup_time'), self.READ_pickup_time_format)
            self.pickup_time = self.pickup_time_dt.strftime(self.WRITE_pickup_time_format)
        except:
            self.pickup_time = order_dict.pop('pickup_time')

        print(self.name)
        print(self.email)
        print()

    def send_confirmation_email(self, config):
        organization_name = config.config_dict['send_email_info']['organization name']
        send_client = emails.SendManager(config.config_dict['send_email_info'])
        text = 'Hi ' + self.name + ',\n\n'
        text += 'Your ' + self.order_type.lower() + ' of ' + self.order + ' has printed succesfully. '
        text += 'It will be ready at ' + self.pickup_time + '.'
        try:
            send_client.send_email(destination = self.email, subject = organization_name + ' - Order Confirmation', msg_content = text)
        except:
            print('Email not sent')

if __name__ == "__main___":
    while True:
        # dummy = true indicates not to actually print orders
        go = Main(dummy = True)
        go.run()
