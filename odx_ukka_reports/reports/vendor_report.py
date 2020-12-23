from dateutil.relativedelta import relativedelta
from odoo import models, fields
import datetime
import dateutil
import io
import base64
import xlwt

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def excel_style(row, col):
    """ Convert given row and column number to an Excel-style cell name. """
    result = []
    while col:
        col, rem = divmod(col - 1, 26)
        result[:0] = LETTERS[rem]
    return ''.join(result) + str(row)


class VendorReport(models.AbstractModel):
    _name = 'report.vendor_report.report.report.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wiz):
        heading_format = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 15,
                                              # 'bg_color': '#0077b3',
                                              })
        value_format = workbook.add_format({'valign': 'center',
                                           'align': 'center',
                                           'size': 10,
                                           'font_color': '#000000'
                                           })

        sub_heading_format_1 = workbook.add_format({'align': 'left',
                                                    'valign': 'vcenter',
                                                    'bold': True, 'size': 12,
                                                    'font_color': '#000000',
                                                    'border': True
                                                    })

        sub_heading_format_2 = workbook.add_format({'align': 'center',
                                                    'valign': 'vcenter',
                                                    'bold': True, 'size': 11.5,
                                                    'bg_color': '#d4d4d3',
                                                    'font_color': '#000000',
                                                    'border': True
                                                    })
        sub_heading_format_3 = workbook.add_format({'align': 'left',
                                                    'valign': 'vcenter',
                                                    'bold': True, 'size': 11.5,
                                                    # 'bg_color': '#d4d4d3',
                                                    'font_color': '#000000',
                                                    'border': True
                                                    })

        col_format = workbook.add_format({'valign': 'left',
                                          'align': 'left',
                                          'bold': True,
                                          'size': 10,
                                          'font_color': '#000000',
                                          })

        col_format.set_text_wrap()
        worksheet = workbook.add_worksheet('Vendor Report')
        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)

        row = 1
        worksheet.set_row(1, 20)
        starting_col = excel_style(row, 1)
        ending_col = excel_style(row, 6)
        worksheet.merge_range('%s:%s' % (starting_col, ending_col),
                              'Vendor Report',
                              heading_format)
        row = row + 1
        worksheet.write(row, 0, "Date From", sub_heading_format_1)
        worksheet.write(row, 1, str(wiz.date_from), sub_heading_format_1)
        worksheet.write(row, 2, "Date To", sub_heading_format_1)
        worksheet.write(row, 3, str(wiz.date_to), sub_heading_format_1)
        row = row + 2

        if wiz.vendor_id:
            vendors = self.env['res.partner'].sudo().search([('id', '=', wiz.vendor_id.id)
                                                        ])
        else:
            vendors = self.env['res.partner'].sudo().search([('supplier_rank', '>=', 1)])

        if wiz.branch_id:
            worksheet.write(row, 0, "Branch", value_format)
            worksheet.write(row, 1, wiz.branch_id.name, value_format)
            row += 1
        new_date = wiz.date_from - datetime.timedelta(days=1)
        date = datetime.datetime.strptime(str(new_date), '%Y-%m-%d')
        difference = (wiz.date_to - wiz.date_from).days
        for i in range(difference + 1):
            date += datetime.timedelta(days=1)
            alternate_date_to = str(date.date()) + ' ' + '23:59:59'
            alternate_date_from = date
            head = row
            flag = False
            row = row + 2

            for rec in vendors:
                if wiz.branch_id:
                    orders = self.env['purchase.order'].search([('partner_id', '=', rec.id),
                                                                ('date_order', '>=', alternate_date_from),
                                                                ('date_order', '<=', alternate_date_to),
                                                                ('state', '=', 'purchase'),
                                                                ('company_id', '=', wiz.branch_id.id)])
                else:
                    orders = self.env['purchase.order'].search([('partner_id', '=', rec.id),
                                                                ('date_order', '>=', alternate_date_from),
                                                                ('date_order', '<=', alternate_date_to),
                                                                ('state', '=', 'purchase')])

                if orders:

                    flag = True
                    amount_total = 0

                    total_sell_price = 0
                    margin_percentage = 0
                    total_orders = 0
                    dates = []
                    for order in orders:
                        total_margin = 0
                        total_orders = total_orders + 1
                        amount_total = amount_total + order.amount_total
                        for line in order.order_line:
                            price_rate = line.product_id.uom_id._compute_price(line.product_id.lst_price, line.product_uom)
                            original_price = line.product_qty * price_rate
                            print(price_rate)
                            sell_price = line.product_qty * line.price_unit
                            total_sell_price = total_sell_price + original_price
                            margin = original_price - sell_price
                            total_margin = total_margin + margin
                            if total_sell_price:
                                margin_percentage = (total_margin / total_sell_price) * 100
                    worksheet.write(row, 0, rec.name, value_format)
                    worksheet.write(row, 1, total_orders, value_format)
                    worksheet.write(row, 2, amount_total, value_format)
                    worksheet.write(row, 3, total_margin, value_format)
                    worksheet.write(row, 4, round(margin_percentage, 2), value_format)
                    row = row + 1

            if flag:
                worksheet.write(head, 0, "Date", sub_heading_format_3)
                worksheet.write(head, 1, str(date.date()), sub_heading_format_3)
                head = head + 1
                worksheet.write(head, 0, "Vendor", sub_heading_format_2)
                worksheet.write(head, 1, "Total Purchase Orders", sub_heading_format_2)
                worksheet.write(head, 2, "Total Order Value", sub_heading_format_2)
                worksheet.write(head, 3, "Total Margin", sub_heading_format_2)
                worksheet.write(head, 4, "Margin %", sub_heading_format_2)
                # row = row +1
                flag = False
            else:
                row = row - 2