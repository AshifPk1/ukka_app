from dateutil.relativedelta import relativedelta

from odoo import models, fields
import datetime
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
    _name = 'report.delivery_time.report.report.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wiz):
        heading_format = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'bold': True,
                                              'size': 15,
                                              })
        value_format = workbook.add_format({'align': 'left',
                                            'valign': 'vcenter',
                                            'bold': False, 'size': 11,
                                            # 'bg_color': '#808080',
                                            # 'font_color': '#808080'
                                            'font_color': '#000000',

                                            })
        sub_heading_format = workbook.add_format({'align': 'center',
                                                  'valign': 'vcenter',
                                                  'bold': True, 'size': 11,
                                                  'bg_color': '#d4d4d3,',
                                                  })
        data_format = workbook.add_format({'valign': 'center',
                                           'align': 'center',
                                           'size': 10,
                                           'font_color': '#000000'
                                           })

        sub_heading_format_1 = workbook.add_format({'align': 'left',
                                                    'valign': 'vcenter',
                                                    'bold': True, 'size': 12,
                                                    'border': True,
                                                    })

        sub_heading_format_2 = workbook.add_format({'align': 'left',
                                                    'valign': 'vcenter',
                                                    'bold': False, 'size': 12,
                                                    'bg_color': '#d4d4d3',
                                                    'font_color': '#000000',
                                                    'border': True
                                                    })

        col_format = workbook.add_format({'valign': 'left',
                                          'align': 'left',
                                          'bold': True,
                                          'size': 10,
                                          'font_color': '#000000',
                                          })

        # from_date = str(wiz.date_from) + ' ' + '00:00:00'
        # to_date = str(wiz.date_to) + ' ' + '23:59:59'

        col_format.set_text_wrap()
        worksheet = workbook.add_worksheet('Delivery Time Report')
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 40)
        worksheet.set_column('E:E', 40)
        worksheet.set_column('F:F', 40)
        worksheet.set_column('G:G', 40)
        worksheet.set_column('H:H', 40)
        worksheet.set_column('I:I', 40)

        row = 1
        worksheet.set_row(1, 20)
        starting_col = excel_style(row, 1)
        ending_col = excel_style(row, 8)
        worksheet.merge_range('%s:%s' % (starting_col, ending_col),
                              'Branch Wise Delivery Time Report',
                              heading_format)
        row = row + 1
        worksheet.write(row, 0, "Start Date", sub_heading_format_1)
        worksheet.write(row, 1, str(wiz.date_from), value_format)
        worksheet.write(row, 2, "End Date", sub_heading_format_1)
        worksheet.write(row, 3, str(wiz.date_to), value_format)
        row = row + 1
        difference = (wiz.date_to - wiz.date_from).days
        inc = 0
        if wiz.branch_id:
            worksheet.write(row, 0, "Branch Name", sub_heading_format_1)
            worksheet.write(row, 1, wiz.branch_id.name, value_format)
            row += 1
        worksheet.write(row, 0, "Date", sub_heading_format)
        worksheet.write(row, 1, "No Of Orders", sub_heading_format)
        worksheet.write(row, 2, "Average Order to Picking Time", sub_heading_format)
        worksheet.write(row, 3, "Average Picking Time", sub_heading_format)
        worksheet.write(row, 4, "Average Delivery Time", sub_heading_format)
        worksheet.write(row, 5, "Average Total Delivery Time", sub_heading_format)
        worksheet.write(row, 6, "Number of ON time delivery", sub_heading_format)
        worksheet.write(row, 7, "Number of late delivery", sub_heading_format)
        worksheet.write(row, 8, "Average Late Time", sub_heading_format)
        row += 1
        for i in range(difference + 1):
            alternate_date = (datetime.datetime.strptime(str(wiz.date_from), '%Y-%m-%d') + datetime.timedelta(
                days=+inc)).strftime(
                '%m-%d-%Y')
            alternate_date_to = str(alternate_date) + ' ' + '23:59:59'
            alternate_date_from = str(alternate_date) + ' ' + '00:00:00'
            deliveries = []
            if wiz.branch_id:
                delivery = self.env['delivery.picking'].sudo().search([
                    ('create_time', '>', alternate_date_from),
                    ('create_time', '<', alternate_date_to),
                    ('company_id', '=', wiz.branch_id.id),
                    ('state','=','confirmed')])

            else:
                delivery = (
                    self.env['delivery.picking'].sudo().search([
                        ('create_time', '>', alternate_date_from),
                        ('create_time', '<', alternate_date_to),
                    ('state','=','confirmed')]))

            if delivery:
                # worksheet.write(row, 0, "Date", sub_heading_format)
                # worksheet.write(row, 1, "No Of Orders", sub_heading_format)
                # worksheet.write(row, 2, "Average Order to Picking Time", sub_heading_format)
                # worksheet.write(row, 3, "Average Picking Time", sub_heading_format)
                # worksheet.write(row, 4, "Average Delivery Time", sub_heading_format)
                # worksheet.write(row, 5, "Average Total Delivery Time", sub_heading_format)
                # worksheet.write(row, 6, "Number of ON time delivery", sub_heading_format)
                # worksheet.write(row, 7, "Number of late delivery", sub_heading_format)
                # worksheet.write(row, 8, "Average Late Time", sub_heading_format)
                # row += 1
                worksheet.write(row, 0, str(alternate_date), data_format)
                qut_pick_difference = relativedelta(days=0,hours=0, minutes=0, seconds=0)
                cre_pick_difference = relativedelta(days=0,hours=0, minutes=0, seconds=0)
                pick_delv_difference = relativedelta(days=0,hours=0, minutes=0, seconds=0)
                for delv in delivery:
                    deliveries.append(delv)
                    print((delv.sale_order_id.create_date,"quotation"))
                    print((delv.create_time,"pickcreate"))
                    print(relativedelta(delv.create_time,delv.sale_order_id.create_date))
                    quotation_time = fields.Datetime.from_string(delv.sale_order_id.create_date)
                    pick_create_time = fields.Datetime.from_string(delv.create_time)
                    pick_confirm_time = fields.Datetime.from_string(delv.picking_time)
                    delivery_time = fields.Datetime.from_string(delv.delivered_time)
                    qut_pick_difference = qut_pick_difference + relativedelta(delv.create_time, delv.sale_order_id.create_date)
                    cre_pick_difference = cre_pick_difference + relativedelta(delv.picking_time, delv.create_time)
                    pick_delv_difference = pick_delv_difference + relativedelta(delv.delivered_time, delv.sale_order_id.create_date)
                quo_delv_difference = qut_pick_difference + cre_pick_difference + pick_delv_difference
                qut_pick_avg_diff = qut_pick_difference / len(deliveries)
                print(qut_pick_avg_diff,"lafkghagkah")
                cre_pick_avg_diff = cre_pick_difference / len(deliveries)
                print(cre_pick_avg_diff, "lafkghagkah")
                pick_delv_avg_diff = pick_delv_difference / len(deliveries)
                print(pick_delv_avg_diff, "lafkghagkah")
                quo_delv_avg_diff = quo_delv_difference / len(deliveries)
                print(quo_delv_avg_diff, "lafkghagkah")
                if quo_delv_avg_diff.days:
                    hrs = 24 * quo_delv_avg_diff.days
                    qut_pick_avg_time = str(hrs) + ':' + str(qut_pick_avg_diff.minutes) + ':' + str(
                        qut_pick_avg_diff.seconds) + ' - Hours'
                elif qut_pick_avg_diff.hours:
                    qut_pick_avg_time = str(qut_pick_avg_diff.hours) + ':' + str(qut_pick_avg_diff.minutes) + ':' + str(
                        qut_pick_avg_diff.seconds) + ' - Hours'
                elif qut_pick_avg_diff.minutes:
                    qut_pick_avg_time = str(qut_pick_avg_diff.hours) + ':' + str(qut_pick_avg_diff.minutes) + ':' + str(
                        qut_pick_avg_diff.seconds) + ' - Minutes'
                else:
                    qut_pick_avg_time = str(qut_pick_avg_diff.hours) + ':' + str(qut_pick_avg_diff.minutes) + ':' + str(
                        qut_pick_avg_diff.seconds) + ' - Seconds'
                if cre_pick_avg_diff.days:
                    hrs = 24 * cre_pick_avg_diff.days
                    cre_pick_avg_time = str(hrs) + ':' + str(cre_pick_avg_diff.minutes) + ':' + str(
                        cre_pick_avg_diff.seconds) + ' - Hours'
                elif cre_pick_avg_diff.hours:
                    cre_pick_avg_time = str(cre_pick_avg_diff.hours) + ':' + str(cre_pick_avg_diff.minutes) + ':' + str(
                        cre_pick_avg_diff.seconds) + ' - Hours'
                elif cre_pick_avg_diff.minutes:
                    cre_pick_avg_time = str(cre_pick_avg_diff.hours) + ':' + str(cre_pick_avg_diff.minutes) + ':' + str(
                        cre_pick_avg_diff.seconds) + ' - Minutes'
                else:
                    cre_pick_avg_time = str(cre_pick_avg_diff.hours) + ':' + str(cre_pick_avg_diff.minutes) + ':' + str(
                        cre_pick_avg_diff.seconds) + ' - Seconds'
                if pick_delv_avg_diff.days:
                    hrs = 24 * pick_delv_avg_diff.days
                    pick_delv_time = str(hrs) + ':' + str(pick_delv_avg_diff.minutes) + ':' + str(
                        pick_delv_avg_diff.seconds) + ' - Hours'
                elif pick_delv_avg_diff.hours:
                    pick_delv_time = str(pick_delv_avg_diff.hours) + ':' + str(pick_delv_avg_diff.minutes) + ':' + str(
                        pick_delv_avg_diff.seconds) + ' - Hours'
                elif pick_delv_avg_diff.minutes:
                    pick_delv_time = str(pick_delv_avg_diff.hours) + ':' + str(pick_delv_avg_diff.minutes) + ':' + str(
                        pick_delv_avg_diff.seconds) + ' - Minutes'
                else:
                    pick_delv_time = str(pick_delv_avg_diff.hours) + ':' + str(pick_delv_avg_diff.minutes) + ':' + str(
                        pick_delv_avg_diff.seconds) + ' - Seconds'
                if quo_delv_avg_diff.days:
                    hrs = 24 * quo_delv_avg_diff.days
                    quo_delv_time = str(hrs) + ':' + str(quo_delv_avg_diff.minutes) + ':' + str(
                        quo_delv_avg_diff.seconds) + ' - Hours'
                elif quo_delv_avg_diff.hours:
                    quo_delv_time = str(quo_delv_avg_diff.hours) + ':' + str(quo_delv_avg_diff.minutes) + ':' + str(
                        quo_delv_avg_diff.seconds) + ' - Hours'
                elif quo_delv_avg_diff.minutes:
                    quo_delv_time = str(quo_delv_avg_diff.hours) + ':' + str(quo_delv_avg_diff.minutes) + ':' + str(
                        quo_delv_avg_diff.seconds) + ' - Minutes'
                else:
                    quo_delv_time = str(quo_delv_avg_diff.hours) + ':' + str(quo_delv_avg_diff.minutes) + ':' + str(
                        quo_delv_avg_diff.seconds) + ' - Seconds'

                worksheet.write(row, 1, len(deliveries), data_format)
                worksheet.write(row, 2, qut_pick_avg_time, data_format)
                worksheet.write(row, 3, cre_pick_avg_time, data_format)
                worksheet.write(row, 4, pick_delv_time, data_format)
                worksheet.write(row, 5, quo_delv_time, data_format)
                on_time_delivery = []
                off_time_delivery = []
                relat_45 = relativedelta(hours=0, minutes=45, seconds=0)
                relat_75 = relativedelta(hours=1, minutes=15, seconds=0)
                total_late_delivery = relativedelta(hours=0, minutes=0, seconds=0)
                for rec in delivery:
                    if rec.sale_order_id.carrier_id.urgent_delivery:
                        quo_time = fields.Datetime.from_string(rec.sale_order_id.date_order)
                        del_time = fields.Datetime.from_string(rec.delivered_time)
                        total = relativedelta(del_time, quo_time)
                        if total.minutes <= relat_45.minutes:
                            on_time_delivery.append(rec)
                        else:
                            total_late_delivery = total_late_delivery + total
                            off_time_delivery.append(rec)
                    else:
                        quo_time = fields.Datetime.from_string(rec.sale_order_id.date_order)
                        del_time = fields.Datetime.from_string(rec.delivered_time)
                        total = relativedelta(del_time, quo_time)
                        if total.hours < relat_75.hours:
                            # total_late_delivery = total_late_delivery + total
                            on_time_delivery.append(rec)
                        elif total.hours == relat_75.hours:
                            if total.minutes <= relat_75.minutes:
                                on_time_delivery.append(rec)
                            else:
                                total_late_delivery = total_late_delivery + total
                                off_time_delivery.append(rec)
                        else:
                            total_late_delivery = total_late_delivery + total
                            off_time_delivery.append(rec)
                worksheet.write(row, 6, len(on_time_delivery), data_format)
                worksheet.write(row, 7, len(off_time_delivery), data_format)
                if total_late_delivery:
                    total_avg_late = total_late_delivery/len(on_time_delivery)
                    if total_avg_late.hours:
                        total_avg_late_time = str(total_avg_late.hours) + ':' + str(total_avg_late.minutes) + ':' + str(
                        total_avg_late.seconds) + ' - Hours'
                    elif total_avg_late.minutes:
                        total_avg_late_time = str(total_avg_late.hours) + ':' + str(total_avg_late.minutes) + ':' + str(
                            total_avg_late.seconds) + ' - Minutes'
                    else:
                        total_avg_late_time = str(total_avg_late.hours) + ':' + str(total_avg_late.minutes) + ':' + str(
                            total_avg_late.seconds) + ' - Seconds'
                    worksheet.write(row, 8, total_avg_late_time, data_format)
                else:
                    worksheet.write(row, 8, 0, data_format)
                row += 1
            inc = inc + 1
