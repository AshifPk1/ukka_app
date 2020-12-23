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


class PeriodicalReport(models.AbstractModel):
    _name = 'report.periodical_all_branch_xlsx_report.report_xlsx'
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
                                                  'bold': True, 'size': 11,
                                                  })
        sub_heading_format_company = workbook.add_format({'align': 'left',
                                                          'valign': 'left',
                                                          'bold': True, 'size': 12,
                                                          })
        sub_heading_format_1 = workbook.add_format({'align': 'left',
                                                    'valign': 'vcenter',
                                                    'bold': True, 'size': 12,
                                                    'border': True
                                                    })
        value_format = workbook.add_format({'align': 'left',
                                            'valign': 'vcenter',
                                            'bold': False, 'size': 11,
                                            # 'bg_color': '#808080',
                                            # 'font_color': '#808080'
                                            'font_color': '#000000',

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
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 17)
        worksheet.set_column('C:C', 18)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 12)
        worksheet.set_column('H:H', 12)
        worksheet.set_column('I:I', 12)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 12)
        worksheet.set_column('L:L', 15)
        worksheet.set_column('M:M', 15)
        worksheet.set_column('N:N', 15)
        worksheet.set_column('O:O', 15)
        worksheet.set_column('P:P', 15)
        worksheet.set_column('Q:Q', 15)
        row = 1
        worksheet.set_row(row, 20)
        starting_col = excel_style(row, 1)
        ending_col = excel_style(row, 14)
        from_date = datetime.datetime.strptime(str(wiz.date_from), '%Y-%m-%d').strftime('%d/%m/%Y')
        to_date = datetime.datetime.strptime(str(wiz.date_to), '%Y-%m-%d').strftime('%d/%m/%Y')

        worksheet.merge_range('%s:%s' % (starting_col, ending_col),
                              "Periodical Report-All Branches",
                              heading_format)
        row += 1
        worksheet.write(row, 0, "Start Date", sub_heading_format_company)
        worksheet.write(row, 1, from_date, sub_heading_format_company)
        worksheet.write(row, 4, "End Date", sub_heading_format_company)
        worksheet.write(row, 5, to_date, sub_heading_format_company)
        if wiz.branch_id:
            worksheet.write(row, 6, "Branch", sub_heading_format_company)
            worksheet.write(row, 7, wiz.branch_id.name, sub_heading_format_company)
        row += 2

        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'bg_color': '#d4d4d3,',
            'valign': 'vcenter',
        })
        difference = (wiz.date_to - wiz.date_from).days
        inc = 0
        worksheet.merge_range('A5:A6', 'Date', merge_format)
        worksheet.merge_range('B5:B6', 'Total # of Orders', merge_format)
        worksheet.merge_range('C5:C6', 'Total Order Values', merge_format)
        worksheet.merge_range('D5:E5', 'NO of App Orders', merge_format)
        worksheet.write(row + 1, 3, "New", merge_format)
        worksheet.write(row + 1, 4, "Repeated", merge_format)
        worksheet.merge_range('F5:G5', 'App Orders Value', merge_format)
        worksheet.write(row + 1, 5, "New", merge_format)
        worksheet.write(row + 1, 6, "Repeated", merge_format)
        worksheet.merge_range('H5:I5', 'NO of Direct Orders', merge_format)
        worksheet.write(row + 1, 7, "New", merge_format)
        worksheet.write(row + 1, 8, "Repeated", merge_format)
        worksheet.merge_range('J5:K5', 'Direct Orders Value', merge_format)
        worksheet.write(row + 1, 9, "New", merge_format)
        worksheet.write(row + 1, 10, "Repeated", merge_format)
        worksheet.merge_range('L5:L6', 'Total Margin', merge_format)
        worksheet.merge_range('M5:M6', 'Delivery Charge', merge_format)
        worksheet.merge_range('N5:N6', 'Total Revenue', merge_format)
        row += 2
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
                # app_order = self.env['sale.order'].sudo().search([('order_method', '=', 'app'),
                #                                                   ('date_order', '>', alternate_date_from),
                #                                                   ('date_order', '<', alternate_date_to),
                #                                                   ('company_id', '=', wiz.branch_id.id)])
                # direct_order = self.env['sale.order'].sudo().search(
                #     [('order_method', '=', 'direct'),
                #      ('date_order', '>', alternate_date_from),
                #      ('date_order', '<', alternate_date_to),
                #      ('company_id', '=', wiz.branch_id.id)])
            else:
                delivery = self.env['delivery.picking'].sudo().search([
                        ('create_time', '>', alternate_date_from),
                        ('create_time', '<', alternate_date_to),('state','=','confirmed')])
                # app_order = self.env['sale.order'].sudo().search([('order_method', '=', 'app'),
                #                                                   ('date_order', '>', alternate_date_from),
                #                                                   ('date_order', '<', alternate_date_to)
                #                                                   ])
                # direct_order = self.env['sale.order'].sudo().search(
                #     [('order_method', '=', 'direct'),
                #      ('date_order', '>', alternate_date_from),
                #      ('date_order', '<', alternate_date_to)])
            if delivery:
                total_order_value = 0
                worksheet.write(row, 0, str(alternate_date), data_format)
                margin = 0
                app_orders = []
                direct_orders = []
                exmple_sale_order =[]
                delivery_charge = 0
                total_sale_price = 0
                for delv in delivery:
                    deliveries.append(delv)

                    total_order_value = total_order_value + delv.total_ordered_amount
                    if delv.sale_order_id:
                        # exmple_sale = self.env['sale.order'].sudo().search([('id','=',delv.sale_order_id.id),('order_method', '=', 'app'),('order_placed', '=', True)])
                        # if exmple_sale:
                        #     exmple_sale_order.append(exmple_sale)
                        # print("example",exmple_sale,delv)
                        app_order = self.env['sale.order'].sudo().search([('id','=',delv.sale_order_id.id),('order_method', '=', 'app'),
                                                                          ('order_placed', '=', True)])
                        direct_order = self.env['sale.order'].sudo().search(
                            [('id','=',delv.sale_order_id.id),('order_method', '=', 'direct')])
                        if app_order:
                            app_orders.append(app_order)
                        else:
                            print(app_order, delv, "apporders")
                        if direct_order:
                            direct_orders.append(direct_order)
                        else:
                            print(direct_order, delv, "directorders")
                        for line in delv.sale_order_id.order_line:
                            if line.product_id.type == 'service':
                                print(line.product_id, "serviceproduct")
                                delivery_charge = delivery_charge + (line.product_uom_qty * line.price_unit)
                            else:
                                price_rate = line.product_id.uom_id._compute_price(line.cost, line.product_uom)
                                line_cost_price = price_rate * line.product_uom_qty
                                cost_price = round(line_cost_price, 2)
                                if line.order_id.order_method == 'direct':
                                    price_unit = line.price_unit * line.product_uom_qty
                                else:
                                    price_unit = line.price_unit
                                sale_price = price_unit - cost_price
                                if line.product_uom_qty:
                                    margin = margin + (sale_price / line.product_uom_qty)
                # if deliveries:
                    # for rec in deliveries:
                    #     print(rec)
                        # app_order=self.env['sale.order'].sudo().search([('order_method', '=', 'app'),
                        #                                                   ('date_order', '>', alternate_date_from),
                        #                                                   ('date_order', '<', alternate_date_to),
                        #                                                   ('delivery_picking_id', '=', rec.id),
                        #                                                 ('order_placed','=',True)])
                        # direct_order=self.env['sale.order'].sudo().search(
                        #     [('order_method', '=', 'direct'),
                        #      ('date_order', '>', alternate_date_from),
                        #      ('date_order', '<', alternate_date_to),
                        #      ('delivery_picking_id', '=', rec.id),
                        #      ('order_placed', '=', True)])
                        # if app_order:
                        #     app_orders.append(app_order)
                        # else:
                        #     print(app_order,rec,"apporders")
                        # if direct_order:
                        #     direct_orders.append(direct_order)
                        # else:
                        #     print(direct_order,rec,"directorders")
                    # print(len(app_orders))
                    # print(len(direct_orders))
                print(len(app_orders))
                print(len(direct_orders))
                # print(exmple_sale_order)
                worksheet.write(row, 1, len(deliveries), data_format)
                worksheet.write(row, 2, total_order_value, data_format)
                new_app_order = []
                repeat_app_order = []
                new_direct_order = []
                repeat_direct_order = []
                app_new_total_value = 0
                app_repeat_total_value = 0
                new_direct_order_value = 0
                direct_direct_order_value = 0
                if app_orders:
                    for app in app_orders:
                        if app.delivery_picking_id:
                            print(app.delivery_picking_id, "appp")
                        existing = self.env['delivery.picking'].sudo().search(
                            [('picking_partner_id', '=', app.partner_id.id)])
                        if existing:
                            if len(existing) == 1:
                                new_app_order.append(app)
                                if app.delivery_picking_id:

                                    app_new_total_value = app_new_total_value + app.delivery_picking_id.total_ordered_amount
                            else:
                                repeat_app_order.append(app)
                                if app.delivery_picking_id:
                                    app_repeat_total_value = app_repeat_total_value + app.delivery_picking_id.total_ordered_amount
                if direct_orders:
                    for direct in direct_orders:
                        print(direct)
                        if direct.delivery_picking_id:
                            print(direct.delivery_picking_id, "delivery")
                        existing = self.env['delivery.picking'].sudo().search(
                            [('picking_partner_id', '=', direct.partner_id.id)])
                        if existing:
                            if len(existing) == 1:
                                new_direct_order.append(direct)
                                if direct.delivery_picking_id:
                                    print("asjgashdgajdgjhagsdhafdgafd", direct.delivery_picking_id.total_ordered_amount)
                                    new_direct_order_value = new_direct_order_value + direct.delivery_picking_id.total_ordered_amount
                            else:
                                if direct.delivery_picking_id:
                                    direct_direct_order_value = direct_direct_order_value + direct.delivery_picking_id.total_ordered_amount
                                repeat_direct_order.append(direct)
                worksheet.write(row, 3, len(new_app_order), data_format)
                worksheet.write(row, 4, len(repeat_app_order), data_format)
                worksheet.write(row, 5, app_new_total_value, data_format)
                worksheet.write(row, 6, app_repeat_total_value, data_format)
                worksheet.write(row, 7, len(new_direct_order), data_format)
                worksheet.write(row, 8, len(repeat_direct_order), data_format)
                worksheet.write(row, 9, new_direct_order_value, data_format)
                worksheet.write(row, 10, direct_direct_order_value, data_format)
                worksheet.write(row, 11, margin, data_format)
                worksheet.write(row, 12, delivery_charge, data_format)
                worksheet.write(row, 13, margin + delivery_charge, data_format)
                row += 2
            inc = inc + 1
