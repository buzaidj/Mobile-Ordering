from escpos.printer import Usb, Dummy
import config
import time


class DummyPrinter(object):
    def __init__(self):
        pass
    # TODO: find a way to clear out this set

    def print_ticket(self, order):
        self.d = Dummy()
        self.d.line_spacing(120)
        self.d.ln(1)

        self.d.set(align = "center", bold = True, underline = 2, double_height = False, double_width = False, custom_size = True, smooth = True, width = 2, height = 2, invert = False, density = 8, font = 'a')
        self.d.block_text(str(order.order_number) + ' ' + order.name + '\n', font = 'a')
        self.d.ln(1)

        self.d.set(align = "center", bold = False, underline = 0, double_height = False, double_width = False, custom_size = True, smooth = True, width = 2, height = 2, invert = False, density = 8, font = 'a')
        self.d.block_text(order.order_type + '\n', columns = 20, font = 'a')
        self.d.ln(1)

        self.d.text(order.formatted_number + '\n')
        self.d.text(order.date + '\n')
        self.d.text(order.time + '\n')
        self.d.text(' \n')

        self.d.set(align = "left", bold = True, underline = 0, double_height = False, double_width = False, custom_size = True, smooth = True, width = 2, height = 2, invert = False, density = 8, font = 'b')
        self.d.text('PICKUP TIME\n')

        self.d.set(align = "left", bold = False, underline = 0, double_height = False, double_width = False, custom_size = True, smooth = True, width = 2, height = 2, invert = False, density = 8, font = 'a')
        self.d.block_text(order.pickup_time + '\n', columns = 20, font = 'a')

        self.d.ln(2)

        self.d.set(align = "left", bold = True, underline = 0, double_height = False, double_width = False, custom_size = True, smooth = True, width = 2, height = 2, invert = False, density = 8, font = 'b')
        self.d.text('ORDER\n')

        self.d.set(align = "left", bold = False, underline = 0, double_height = False, double_width = False, custom_size = True, smooth = True, width = 2, height = 2, invert = False, density = 8, font = 'a')
        self.d.block_text(order.order + '\n', columns = 20, font = 'a')

        self.d.ln(2)

        if order.notes != '':
            self.d.set(align = "left", bold = True, underline = 0, double_height = False, double_width = False, custom_size = True, smooth = True, width = 2, height = 2, invert = False, density = 8, font = 'b')
            self.d.text('NOTES\n')

            self.d.set(align = "left", bold = False, underline = 0, double_height = False, double_width = False, custom_size = True, smooth = True, width = 2, height = 2, invert = False, density = 8, font = 'a')
            self.d.block_text(order.notes + '\n', columns = 20, font = 'a')

        self.d.cut()

    def print_error_message(self, error_message):
        pass

"""
Inherits the DummyPrinter class for a not connected printer
"""
class UsbPrinter(DummyPrinter):
    """
    Initialize USB printer with vendor ID and product ID
    """
    def __init__(self, config):
        super().__init__()
        vendor_id = int(config.config_dict['printer_config']['usb']['vendor_id'],16)
        product_id = int(config.config_dict['printer_config']['usb']['product_id'],16)
        self.p = None
        while self.p == None:
            try:
                self.p = Usb(vendor_id, product_id)

            except Exception as e:
                print(e)
                print("Trying again in 15 seconds")
                time.sleep(15)

    def print_ticket(self, order):
        super().print_ticket(order)
        y = True
        while y:
            try:
                self.p._raw(self.d.output)
                y = False
            except:
                print("might be reloading paper")
                time.sleep(10)
