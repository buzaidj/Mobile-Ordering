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
                self.client = pygsheets.authorize(service_file='client_secret.json')
                self.sheets = []
                for name, params in config.config_dict['gsheets_info'].items():
                    sheet_name = params['spreadsheet_name']
                    format = params['format']
                    sh = self.client.open(sheet_name).sheet1
                    gsheet = GSheet(name, format, sh)
                    self.sheets.append(gsheet)
                done = True
            except Exception as e:
                email_error = emails.SendManager(config.config_dict['send_email_info'])
                email_error.send_email(config.config_dict['send_email_info']['send status emails to'], subject = 'Error in initializing sheet', msg_content = str(e))
                time.sleep(30)

    def refresh_sheets(self, config):
        r = None
        while r == None:
            try:
                for gsheet in self.sheets:
                    gsheet.sheet.refresh()
                    time.sleep(2)
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
                                f = False
                            except Exception as e:
                                try:
                                    print('ERROR')
                                    email_error = emails.SendManager(config.config_dict['send_email_info'])
                                    email_error.send_email(config.config_dict['send_email_info']['send status emails to'], subject = 'Error in getting sheet cells', msg_content = str(e))
                                    time.sleep(5)
                                except:
                                    time.sleep(5)



                        order_dict['order_type'] = gsheet.name.capitalize() + ' Order'
                        order_dict['order_number'] = gsheet.index % 100
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

    def clear_sheets(self):
        for gsheet in self.sheets:
            if gsheet.name == 'dinner':
                gsheet.sheet.clear('A2', fields = '*')
                gsheet.index_cell.set_value(2)
                gsheet.index = 2
