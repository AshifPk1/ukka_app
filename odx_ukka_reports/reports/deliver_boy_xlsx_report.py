import parser

from dateutil.relativedelta import relativedelta

from odoo import models, fields
import datetime
import io
import sys
import pytz
import base64

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def excel_style(row, col):
    """ Convert given row and column number to an Excel-style cell name. """
    result = []
    while col:
        col, rem = divmod(col - 1, 26)
        result[:0] = LETTERS[rem]
    return ''.join(result) + str(row)


class DeliveryBoyReport(models.AbstractModel):
    _name = 'report.delivery_boy_xlsx_report.report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wiz):

        date_to = str(wiz.date_to) + ' ' + '23:59:59'
        date_from = str(wiz.date_from) + ' ' + '00:00:00'
        heading_format = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 15,
                                              })
        sub_heading_format = workbook.add_format({'align': 'center',
                                                  'valign': 'vcenter',
                                                  'bg_color': '#d4d4d3,',
                                                  'bold': True, 'size': 11,
                                                  })
        sub_heading_format_company = workbook.add_format({'align': 'left',
                                                          'valign': 'left',
                                                          'bold': True, 'size': 12,
                                                          })
        sub_heading_format_company_new = workbook.add_format({'align': 'left',
                                                          'valign': 'left',

                                                          'bold': True, 'size': 12,
                                                          })

        col_format = workbook.add_format({'valign': 'left',
                                          'align': 'left',
                                          'bold': True,
                                          'size': 10,
                                          'font_color': '#000000'
                                          })
        data_format = workbook.add_format({'valign': 'center',
                                           'align': 'center',
                                           'size': 10,
                                           'font_color': '#000000'
                                           })
        col_format.set_text_wrap()
        worksheet = workbook.add_worksheet('Delivery Boy Sheet')
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 18)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 25)
        worksheet.set_column('G:G', 10)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 10)
        worksheet.set_column('L:L', 15)
        worksheet.set_column('M:M', 15)
        worksheet.set_column('N:N', 15)
        worksheet.set_column('O:O', 15)
        worksheet.set_column('P:P', 20)
        worksheet.set_column('Q:Q', 20)
        row = 1
        worksheet.set_row(row, 20)
        starting_col = excel_style(row, 1)
        ending_col = excel_style(row, 5)
        from_date = datetime.datetime.strptime(str(wiz.date_from), '%Y-%m-%d').strftime('%d/%m/%Y')
        to_date = datetime.datetime.strptime(str(wiz.date_to), '%Y-%m-%d').strftime('%d/%m/%Y')

        worksheet.merge_range('%s:%s' % (starting_col, ending_col),
                              "Delivery Boy Branch Wise",
                              heading_format)
        row += 1
        worksheet.write(row, 0, "Start Date", sub_heading_format_company)
        worksheet.write(row, 1, from_date, data_format)
        worksheet.write(row, 3, "End Date", sub_heading_format_company)
        worksheet.write(row, 4, to_date, data_format)
        row += 1
        difference = (wiz.date_to - wiz.date_from).days
        if wiz.branch_id:
            worksheet.write(row, 0, "Branch", sub_heading_format_company_new)
            worksheet.write(row, 1, wiz.branch_id.name, data_format)
            row += 1

        inc = 0
        for i in range(difference + 1 ):
            alternate_date = (datetime.datetime.strptime(str(wiz.date_from), '%Y-%m-%d') + datetime.timedelta(
                days=+inc)).strftime(
                '%m-%d-%Y')
            alternate_date_to = str(alternate_date) + ' ' + '23:59:59'
            alternate_date_from = str(alternate_date) + ' ' + '00:00:00'
            pickings = []
            deliveries = []
            flag = False
            head = row
            row = row +3
            if wiz.deliver_boy:
                delivery_boys = self.env['res.partner'].sudo().search(
                    [('id', '=', wiz.deliver_boy.id), ('is_delivery', '=', True)])
            else:
                delivery_boys = self.env['res.partner'].sudo().search([('id', '!=', False), ('is_delivery', '=', True)])

            if delivery_boys:
                for rec in delivery_boys:
                    if wiz.branch_id:
                        picking = (self.env['delivery.picking'].sudo().search([('pick_up_boy_id.picking_boy_id', '=', rec.id),
                                                                        ('create_time', '>', alternate_date_from),
                                                                        ('create_time', '<', alternate_date_to),
                                                                        ('company_id', '=', wiz.branch_id.id)]))
                        delivery = (
                            self.env['delivery.picking'].sudo().search([('delivery_boys_id.picking_boy_id', '=', rec.id),
                                                                 ('create_time', '>', alternate_date_from),
                                                                 ('create_time', '<', alternate_date_to),
                                                                 ('company_id', '=', wiz.branch_id.id)]))
                        if picking or delivery:
                            flag =True

                    else:
                        picking = (self.env['delivery.picking'].sudo().search([('pick_up_boy_id.picking_boy_id', '=', rec.id),
                                                                        ('create_time', '>', alternate_date_from),
                                                                        ('create_time', '<', alternate_date_to)]))
                        delivery = (
                            self.env['delivery.picking'].sudo().search([('delivery_boys_id.picking_boy_id', '=', rec.id),
                                                                 ('create_time', '>', alternate_date_from),
                                                                 ('create_time', '<', alternate_date_to)]))
                        if picking or delivery:
                            flag = True

                    if picking:
                        total_avg_time_picking = 0
                        difference = relativedelta(hours=0, minutes=0, seconds=0)
                        for pick in picking:
                            pickings.append(pick)
                            d1 = fields.Datetime.from_string(pick.picking_time)
                            d2 = fields.Datetime.from_string(pick.create_time)
                            difference = difference + relativedelta(d1, d2)
                        avg_diff = difference / len(pickings)
                        if avg_diff.days:
                            hrs = 24 * avg_diff.days
                            total_avg_time_picking = str(hrs) + ':' + str(avg_diff.minutes) + ':' + str(
                                avg_diff.seconds) + ' - Hours'
                        elif avg_diff.hours:
                            total_avg_time_picking = str(avg_diff.hours) + ':' + str(
                                avg_diff.minutes) + ':' + str(
                                avg_diff.seconds) + ' - Hours'
                        elif avg_diff.minutes:
                            total_avg_time_picking = str(avg_diff.hours) + ':' + str(
                                avg_diff.minutes) + ':' + str(
                                avg_diff.seconds) + ' - Minutes'
                        else:
                            total_avg_time_picking = str(avg_diff.hours) + ':' + str(
                                avg_diff.minutes) + ':' + str(
                                avg_diff.seconds) + ' - Seconds'
                        # if not avg_diff.hours and not avg_diff.minutes and avg_diff.seconds:
                        #     total_avg_time_picking = str(avg_diff.hours) + ':' + str(avg_diff.minutes) + ':' + str(
                        #         avg_diff.seconds) + ' - Seconds'
                        # elif not avg_diff.hours and avg_diff.minutes:
                        #     total_avg_time_picking = str(avg_diff.hours) + ':' + str(avg_diff.minutes) + ':' + str(
                        #         avg_diff.seconds) + ' - Minutes'
                        # elif avg_diff.hours:
                        #     total_avg_time_picking = str(avg_diff.hours) + ':' + str(avg_diff.minutes) + ':' + str(
                        #         avg_diff.seconds) + ' - Hours'

                        worksheet.write(row, 0, rec.name, data_format)
                        worksheet.write(row, 1, len(pickings), data_format)
                        worksheet.write(row, 2, total_avg_time_picking, data_format)
                    if delivery:
                        for delv in delivery:
                            print(delv)
                            deliveries.append(delv)
                            d3 = fields.Datetime.from_string(delv.delivered_time)
                            d4 = fields.Datetime.from_string(delv.picking_time)
                            difference = difference + relativedelta(d3, d4)
                        avg_diff = difference / len(deliveries)
                        # if not avg_diff.hours and not avg_diff.minutes and avg_diff.seconds:
                        #     total_avg_time = str(avg_diff.hours) + ':' + str(avg_diff.minutes) + ':' + str(
                        #         avg_diff.seconds) + '- Seconds'
                        # elif not avg_diff.hours and avg_diff.minutes:
                        #     total_avg_time = str(avg_diff.hours) + ':' + str(avg_diff.minutes) + ':' + str(
                        #         avg_diff.seconds) + '- Minutes'
                        # else:
                        #     total_avg_time = str(avg_diff.hours) + ':' + str(avg_diff.minutes) + ':' + str(
                        #         avg_diff.seconds) + '- Hours'
                        if avg_diff.days:
                            hrs = 24 * avg_diff.days
                            total_avg_time = str(hrs) + ':' + str(avg_diff.minutes) + ':' + str(
                                avg_diff.seconds) + ' - Hours'
                        elif avg_diff.hours:
                            total_avg_time = str(avg_diff.hours) + ':' + str(
                                avg_diff.minutes) + ':' + str(
                                avg_diff.seconds) + ' - Hours'
                        elif avg_diff.minutes:
                            total_avg_time = str(avg_diff.hours) + ':' + str(
                                avg_diff.minutes) + ':' + str(
                                avg_diff.seconds) + ' - Minutes'
                        else:
                            total_avg_time = str(avg_diff.hours) + ':' + str(
                                avg_diff.minutes) + ':' + str(
                                avg_diff.seconds) + ' - Seconds'
                        worksheet.write(row, 0, rec.name, data_format)
                        worksheet.write(row, 3, len(delivery), data_format)
                        worksheet.write(row, 4, total_avg_time, data_format)
                        row += 1

                if flag:
                    head = head + 1
                    worksheet.write(head, 0, "Date:", sub_heading_format_company_new)
                    worksheet.write(head, 1, str(alternate_date), data_format)
                    head = head + 1
                    worksheet.write(head, 0, "Deliver Boy", sub_heading_format)
                    worksheet.write(head, 1, "No of Picking", sub_heading_format)
                    worksheet.write(head, 2, "Average Picking Time", sub_heading_format)
                    worksheet.write(head, 3, "No of Delivery", sub_heading_format)
                    worksheet.write(head, 4, "Average Delivery Time", sub_heading_format)
                    row = row + 1
                    flag = False
                else:
                    row = row - 3
            inc = inc + 1
