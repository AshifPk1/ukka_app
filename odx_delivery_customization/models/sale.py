from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID
from datetime import date
from datetime import datetime
from odoo.http import request
import html2text
import threading


class ConvertHtmlText(object):

    def convert_html_to_text(result_txt):
        capt = b'%s' % (result_txt)
        convert_byte_to_str = capt.decode('utf-8')
        return html2text.html2text(convert_byte_to_str)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _order = 'order_placed_date desc'

    picking_boy_id = fields.Many2one(comodel_name='res.partner', string="Picking Boy",
                                     domain=[('is_delivery', '=', True)])

    delivery_boy_id = fields.Many2one(comodel_name='res.partner', string="Delivery Boy",
                                      domain=[('is_delivery', '=', True)])
    delivery_picking_id = fields.Many2one('delivery.picking', string="Picking/Delivery Details", copy=False)
    pick_up_boy_id = fields.Many2one(comodel_name='work.details', string="Picking Boy",
                                     domain=[('state', '=', 'done')], copy=False)
    delivery_boys_id = fields.Many2one(comodel_name='work.details', string="Delivery Boy",
                                       domain=[('state', '=', 'done')], copy=False)
    payment_id = fields.Many2one(comodel_name='account.payment', string="Payment Details")
    is_credit = fields.Boolean(string="Credited")
    is_paid = fields.Boolean(string="Paid")
    order_method = fields.Selection([
        ('app', 'Mobile App'),
        ('website', 'Ecommerce'),
        ('direct', 'Direct')
    ],
        string='Order Method', default='direct', copy=False)
    order_placed = fields.Boolean(string="Order Placed")
    delivery_time_slots = fields.Many2one('delivery.time.slot', string="Delivery Time Slot")
    completed_delivery = fields.Boolean(string="Completed Delivery", compute="_check_delivery")
    cancelled_order = fields.Boolean(string="Canceled Order")
    payment_methods = fields.Selection([
        ('cod', 'Cash On Delivery'),
        ('upi', 'UPI Payment'),

    ],
        string='Payment Method')

    transaction_id = fields.Char(string="Transaction ID")
    payment_amount = fields.Float(string="Order Amount")
    shipping_schedule = fields.Boolean(string="Scheduled Delivery", compute="_check_schedule_boolean")
    shipping_urgent = fields.Boolean(string="Urgent Delivery", compute="_check_urgent_boolean")
    order_placed_date = fields.Datetime(string="Order Placed On")
    delivery_status = fields.Selection([
        ('pending', 'Ready for PickUp'),
        ('ready', 'Ready To Deliver'),
        ('confirmed', 'Delivered')], string='Delivery Status', index=True, related='delivery_picking_id.state')

    @api.depends('delivery_picking_id')
    def _check_delivery(self):
        for record in self:
            if record.delivery_picking_id.state == 'confirmed':
                record.completed_delivery = True
            else:
                record.completed_delivery = False

    @api.depends('carrier_id')
    def _check_schedule_boolean(self):
        for record in self:
            if record.carrier_id.scheduled_delivery:
                record.shipping_schedule = True
            else:
                record.shipping_schedule = False

    @api.depends('carrier_id')
    def _check_urgent_boolean(self):
        for record in self:
            if record.carrier_id.urgent_delivery:
                record.shipping_urgent = True
            else:
                record.shipping_urgent = False

    def invoice_payment_reconcile(self):

        invoice_lines = []

        if self.invoice_ids:

            if self.invoice_ids.state == 'posted':
                for line in self.invoice_ids.line_ids:
                    invoice_lines.append(line)

        payment_lines = []
        if self.payment_id:
            if self.payment_id.state == 'posted':
                for line in self.payment_id.move_line_ids:
                    payment_lines.append(line)
        invoice_lines += payment_lines

        # PAYMENT AND INVOICE LINES RECONCILES
        account_move_lines_to_reconcile = self.env['account.move.line']
        for line in invoice_lines:

            if line.account_id.internal_type == 'receivable':
                account_move_lines_to_reconcile |= line

            account_move_lines_to_reconcile.filtered(lambda l: l.reconciled == False).reconcile()

    def create_payment(self):
        """ Create a register payment """

        payment_id = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'amount': self.invoice_ids.amount_total,

            'payment_date': self.create_date,

            'communication': '%s-%s' % (self.name, self.partner_id.name),
            'journal_id': self.delivery_picking_id.payment_method_id.id,
            'invoice_ids': [(4, self.invoice_ids.id, None)],

        })

        payment_id.post()
        self.payment_id = payment_id.id

    # CREATE INVOICES after SALE ORDER CONFIRMATION
    def create_sale_invoices(self):
        for record in self:

            if record.invoice_ids:
                raise UserError(_('Invoice already created!'))

            else:
                if not record.delivery_picking_id.state == 'confirmed':
                    raise UserError(_('Please complete the delivery process to make invoice'))
                if record.delivery_picking_id:

                    if record.is_paid:
                        # self._create_invoices()
                        invoice = record._create_invoices()

                        invoice.action_post()
                        record.create_payment()
                        record.invoice_payment_reconcile()

                    if record.is_credit:
                        invoice = record._create_invoices()

                        invoice.action_post()
                else:

                    raise UserError(_('Please create delivery order to make invoice!'))

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.delivery_picking_id.payment_method_id:
            res['journal_id'] = self.delivery_picking_id.payment_method_id.id
        res['sale_id'] = self.id
        res['ref'] = self.name
        res['company_id'] = self.company_id.id

        return res

    # @api.onchange('pick_up_boy_id', 'delivery_boys_id')
    # def working_boys_now(self):
    #
    #     # today = date.today()
    #     # check_date_end = str(today) + ' ' + '23:59:59'
    #     # check_date_start = str(today) + ' ' + '00:00:00'
    #
    #     return {'domain': {'pick_up_boy_id': [('starting_time','<=',check_date_end),('starting_time','>=',check_date_start),('state', '=', 'done')],
    #                        'delivery_boys_id': [('starting_time','<=',check_date_end),('starting_time','>=',check_date_start), ('state', '=', 'done')]}
    #             }

    # CREATE DELIVERY PICKING MODEL FROM SALE ORDER
    def ready_for_picking(self):
        for record in self:
            picking_lines = []
            categories = []
            vendor_list = []
            values = {}
            delivery_charg = 0
            discount_vals = 0
            shipping_addr = record.partner_id
            if record.partner_id.child_ids:
                for child in record.partner_id.child_ids:
                    if child.selected_address:
                        shipping_addr = child

            delivery_picking_obj = self.env['delivery.picking']

            if record.order_line:
                for line in record.order_line:
                    if line.product_uom_qty:
                        line.write({
                            'initial_order_qty' : line.product_uom_qty
                        })
                    if line.product_id.seller_ids and not line.product_id.type == 'service':
                        if line.product_id.seller_ids[0].name not in vendor_list:
                            vendor_list.append(line.product_id.seller_ids[0].name)
                    else:
                        if line.product_id.categ_id and not line.product_id.type == 'service':
                            if line.product_id.categ_id not in categories:
                                categories.append(line.product_id.categ_id)

                for vendor in vendor_list:
                    values = {
                        'name': vendor.name,
                        'display_type': 'line_section',

                    }
                    picking_lines.append((0, 0, values))
                    for line in record.order_line:
                        if line.product_id.type == 'service':
                            if line.is_delivery:
                                delivery_charg = line.price_subtotal
                            if line.price_unit < 0:
                                discount_vals = line.price_subtotal

                        if line.product_id.seller_ids:

                            if line.product_id.seller_ids[0].name == vendor and not line.product_id.type == 'service':
                                values = {
                                    'product_id': line.product_id.id,
                                    'product_qty': line.product_uom_qty,
                                    'product_uom': line.product_uom.id,
                                    'price_subtotal': line.price_subtotal,
                                    'total_ordred_qty': line.app_ordered_qty,
                                    'mrp': line.price_unit,

                                    'sale_order_line_id': line.id,
                                    'sale_order_id': line.order_id.id,
                                    'vendor_id': line.product_id.seller_ids[0].name.id

                                }
                                picking_lines.append((0, 0, values))

                for category in categories:
                    values = {
                        'name': category.name,
                        'display_type': 'line_section',

                    }
                    picking_lines.append((0, 0, values))

                    for line in record.order_line:
                        if line.product_id.type == 'service':
                            if line.is_delivery:
                                delivery_charg = line.price_subtotal
                            if line.price_unit < 0:
                                discount_vals = line.price_subtotal
                        if not line.product_id.seller_ids and not line.product_id.type == 'service':
                            if line.product_id.categ_id == category:
                                values = {
                                    'product_id': line.product_id.id,
                                    'product_qty': line.product_uom_qty,
                                    'product_uom': line.product_uom.id,
                                    'price_subtotal': line.price_subtotal,
                                    'total_ordred_qty': line.app_ordered_qty,

                                    'mrp': line.price_unit,

                                    'sale_order_line_id': line.id,
                                    'sale_order_id': line.order_id.id,

                                }
                                picking_lines.append((0, 0, values))
            else:
                raise UserError(_('Please select products to deliver'))
            vals = {
                'sale_order_id': record.id,
                'delivery_boys_id': record.delivery_boys_id.id if record.delivery_boys_id else False,
                'pick_up_boy_id': record.pick_up_boy_id.id if record.pick_up_boy_id else False,
                'picking_partner_id': record.partner_id.id,
                'company_id': record.company_id.id,
                'mobile_number': shipping_addr.mobile if shipping_addr.mobile else False,
                'street': shipping_addr.street2 if shipping_addr.street2 else False,
                'city': shipping_addr.city if shipping_addr.city else False,
                'customer_name': shipping_addr.name if shipping_addr.name else False,
                'zip': shipping_addr.zip if shipping_addr.zip else False,
                'address': shipping_addr.street if shipping_addr.street else False,
                'location_link': shipping_addr.location_link if shipping_addr.location_link else False,
                'delivery_charges': delivery_charg,
                'discount': discount_vals,
                'total_ordered_amount': record.amount_total,
                'picking_lines_ids': picking_lines,

            }
            delivery = delivery_picking_obj.create(vals)
            record.delivery_picking_id = delivery.id

            ctx = {'create': False}
            return {
                'name': 'Picking Details',
                'res_model': 'delivery.picking',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': delivery.id,
                'view_id': self.env.ref("odx_delivery_customization.delivery_picking_form_view").id,
                'context': ctx,

            }

    # UPDATE ORDERS FROM SALE ORDER
    def delivery_orders_update(self):
        for record in self:


            if not record.delivery_picking_id.state == 'confirmed':

                order_line_ids = []
                delivery_lines = []

                for ord_line in record.order_line:
                    order_line_ids.append(ord_line.id)
                # print(order_line_ids,"order_lines")
                if record.delivery_picking_id.picking_lines_ids:
                    for lines_id in record.delivery_picking_id.picking_lines_ids:
                        if lines_id.product_id:
                            delivery_lines.append(lines_id.sale_order_line_id.id)

                ord_line = []
                vendor_list = []
                categories = []
                for order_line in order_line_ids:
                    if order_line not in delivery_lines:
                        ord_line.append(order_line)
                if ord_line:
                    for sale_line in ord_line:
                        # print("trueeeeeee")
                        line_id = self.env['sale.order.line'].search([('id', '=', sale_line)])
                        if line_id.product_id.seller_ids:
                            if line_id.product_id.seller_ids[0].name not in vendor_list:
                                vendor_list.append(line_id.product_id.seller_ids[0].name)
                        else:
                            if line_id.product_id.categ_id not in categories:
                                categories.append(line_id.product_id.categ_id)

                for vendor in vendor_list:

                    record.delivery_picking_id.write({
                        'picking_lines_ids': [(0, 0, {
                            'name': vendor.name,
                            'display_type': 'line_section',
                        })]
                    })
                    for sale_line in ord_line:
                        line_id = self.env['sale.order.line'].search([('id', '=', sale_line)])
                        if line_id.product_id.seller_ids and not line_id.product_id.type == 'service':

                            if line_id.product_id.seller_ids[0].name == vendor:
                                record.delivery_picking_id.write({
                                    'picking_lines_ids': [(0, 0, {

                                        'product_id': line_id.product_id.id,
                                        'product_qty': line_id.product_uom_qty,
                                        'price_subtotal': line_id.price_subtotal,

                                        'mrp': line_id.price_unit,

                                        'sale_order_line_id': line_id.id,
                                        'sale_order_id': line_id.order_id.id,
                                        'update_order': 1

                                    })],
                                    'total_ordered_amount': record.amount_total
                                })
                for category in categories:
                    for sale_line in ord_line:
                        line_id = self.env['sale.order.line'].search([('id', '=', sale_line)])


                        if not line_id.product_id.seller_ids and not line_id.product_id.type == 'service':
                            record.delivery_picking_id.write({
                                'picking_lines_ids': [(0, 0, {
                                    'name': category.name,
                                    'display_type': 'line_section',
                                })]
                            })

                            if line_id.product_id.categ_id == category and not line_id.product_id.type == 'service':
                                record.delivery_picking_id.write({
                                    'picking_lines_ids': [(0, 0, {

                                        'product_id': line_id.product_id.id,
                                        'product_qty': line_id.product_uom_qty,
                                        'price_subtotal': line_id.price_subtotal,

                                        'mrp': line_id.price_unit,

                                        'sale_order_line_id': line_id.id,
                                        'sale_order_id': line_id.order_id.id,
                                        'update_order': 1,

                                    })],
                                    'total_ordered_amount': record.amount_total
                                })

                # print(ord_line, "order_line not")
                if record.delivery_picking_id:
                    for sale_ordr_line in record.order_line:
                        if sale_ordr_line.product_id.type == 'service':
                            if sale_ordr_line.is_delivery:
                                if record.delivery_picking_id.delivery_charges != sale_ordr_line.price_subtotal:
                                    record.delivery_picking_id.write({'delivery_charges': sale_ordr_line.price_subtotal,
                                                                      'total_ordered_amount': record.amount_total})
                            if sale_ordr_line.price_unit < 0:
                                if record.delivery_picking_id.discount != sale_ordr_line.price_subtotal:
                                    record.delivery_picking_id.write({'discount': sale_ordr_line.price_subtotal,
                                                                      'total_ordered_amount': record.amount_total})

                if record.delivery_picking_id.picking_lines_ids:
                    for line in record.delivery_picking_id.picking_lines_ids:
                        if line.product_qty != line.sale_order_line_id.product_uom_qty:
                            line.sale_order_line_id.write({
                                'initial_order_qty' : line.sale_order_line_id.product_uom_qty
                            })
                        if line.product_qty != line.sale_order_line_id.product_uom_qty or line.mrp != line.sale_order_line_id.price_unit or line.product_uom != line.sale_order_line_id.product_uom and not line.sale_order_line_id.is_delivery:
                            line.write({'product_qty': line.sale_order_line_id.product_uom_qty,
                                        'mrp': line.sale_order_line_id.price_unit,
                                        'price_subtotal': line.sale_order_line_id.price_subtotal,
                                        'product_uom': line.sale_order_line_id.product_uom,
                                        'returned_qty':0,
                                        'update_order': line.update_order + 1
                                        })

                            if line.update_order > 0:
                                record.delivery_picking_id.total_ordered_amount = record.amount_total

                                subtype_id = self.env['mail.message.subtype'].search([('name', '=', 'Note')])
                                self.env['mail.message'].create({
                                    'body': _(
                                        'The order has been updated.The quantity of product %s is updated to %s with mrp %s') % (
                                                line.sale_order_line_id.product_id.name
                                                , line.sale_order_line_id.product_uom_qty,
                                                line.sale_order_line_id.price_unit),
                                    'model': 'delivery.picking',
                                    'message_type': 'comment',
                                    'res_id': self.delivery_picking_id.id,
                                    'subtype_id': subtype_id.id,
                                })

                # print(delivery_lines,"delivery_lines")


            else:
                raise UserError(_('Order is already delivered.You cannot update a delivered order!'))



    def picking_delivery_view(self):
        for record in self:
            ctx = {'create': False, 'delete': False}
            return {
                'name': 'Picking Details',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': record.delivery_picking_id.id,
                'res_model': 'delivery.picking',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': ctx,

            }

    # CREATE PO FROM SALE ORDER CONFIRMATION BASED ON VENDORS IN PRODUCTS
    def create_rfq(self):

        for record in self:
            vendor_list = []
            purchase = ''
            purchase_order_line_obj = self.env['purchase.order.line']
            purchase_order_obj = self.env['purchase.order']
            if record.order_line:

                prodct_lst = []
                product_list = []
                products = ''
                produts = ''
                for sale_order_line in record.order_line:
                    # TO GET VENDOR LIST TO CREATE PO
                    if sale_order_line.product_id.seller_ids:
                        for seller in sale_order_line.product_id.seller_ids:
                            if sale_order_line.product_id.seller_ids[0].name not in vendor_list:
                                vendor_list.append(seller[0].name)

                    # TO SHOW POP UP MSGS FOR COST ZERO AND NO VENDOR PRODTS
                    if sale_order_line.product_id.standard_price == 0 and not sale_order_line.product_id.type == 'service':
                        if sale_order_line.product_id not in product_list:
                            product_list.append(sale_order_line.product_id)
                    if not sale_order_line.product_id.seller_ids and not sale_order_line.product_id.type == 'service':

                        if sale_order_line.product_id not in prodct_lst:
                            prodct_lst.append(sale_order_line.product_id)

                for prdts in prodct_lst:
                    produts += ' ' + prdts.name + ','
                if produts:
                    raise UserError(_('Please add vendors for the following products %s.') % (produts))

                for prdt in product_list:
                    products += ' ' + prdt.name + ','
                if products:
                    raise UserError(_('Please add cost price for the following products %s.') % (products))

            if record.delivery_picking_id.picking_lines_ids:
                for lines in record.delivery_picking_id.picking_lines_ids:

                    if not lines.is_outside and not lines.display_type == 'line_section':
                        sale_refs = []
                        po = False
                        for vendor in vendor_list:
                            if lines.product_id.seller_ids:
                                if lines.product_id.seller_ids[0].name.id == vendor.id:
                                    if not vendor.outside_purchase:
                                        po = self.env['purchase.order'].sudo().search(
                                            [('state', '=', 'draft'), ('partner_id.outside_purchase', '=', False),
                                             ('partner_id', '=', vendor.id), ('company_id', '=', record.company_id.id)],
                                            limit=1)

                                        if po:
                                            # print("hello")
                                            flag = False
                                            source_list = []
                                            # TODO  code shorten
                                            if po.sale_ref:
                                                source_list = po.sale_ref.split(',')
                                            for doc in source_list:
                                                if doc == record.name:
                                                    flag = True
                                            if not flag:
                                                sale_reff = ' '
                                                if po.sale_ref and record.name:
                                                    po.write({
                                                        'sale_ref': po.sale_ref + ',' + record.name
                                                    })
                                                else:
                                                    po.write({
                                                        'sale_ref': sale_reff
                                                    })
                                            for line in po.order_line:
                                                if line.product_id == lines.product_id:
                                                    quantity = 0
                                                    if lines.sale_order_line_id and lines.sale_order_line_id.product_uom and line.product_uom != lines.sale_order_line_id.product_uom:
                                                        # changing qty from sale order based on uom
                                                        quantity = lines.sale_order_line_id.product_uom._compute_quantity(
                                                            lines.sale_order_line_id.product_uom_qty,
                                                            line.product_uom)
                                                        line.product_qty = quantity + line.product_qty
                                                    else:
                                                        line.product_qty = line.product_qty + lines.sale_order_line_id.product_uom_qty
                                            if not any(line.product_id == lines.product_id for line in po.order_line):
                                                quantity = 0
                                                if lines.sale_order_line_id and lines.sale_order_line_id.product_uom:
                                                    quantity = lines.sale_order_line_id.product_uom._compute_quantity(
                                                        lines.sale_order_line_id.product_uom_qty,
                                                        lines.product_id.uom_id)
                                                purchase_order_line = purchase_order_line_obj.create({

                                                    'product_id': lines.product_id.id,
                                                    'product_qty': quantity,
                                                    'price_unit': lines.product_id.standard_price,
                                                    'price_subtotal': lines.price_subtotal,
                                                    'name': lines.product_id.name,
                                                    "order_id": po.id,
                                                    'product_uom': lines.product_id.uom_id.id,
                                                    "date_planned": datetime.today(),
                                                    "company_id": po.company_id.id

                                                })


                                        else:

                                            purchase_order = purchase_order_obj.create({
                                                "partner_id": vendor.id,
                                                "sale_ref": record.name,
                                                "company_id": record.company_id.id

                                            })
                                            quantity = 0
                                            if lines.sale_order_line_id and lines.sale_order_line_id.product_uom:
                                                quantity = lines.sale_order_line_id.product_uom._compute_quantity(
                                                    lines.sale_order_line_id.product_uom_qty,
                                                    lines.product_id.uom_id)
                                            purchase_order_line = purchase_order_line_obj.create({

                                                'product_id': lines.product_id.id,
                                                'product_qty': quantity,
                                                'price_unit': lines.product_id.standard_price,
                                                'price_subtotal': lines.price_subtotal,
                                                'name': lines.product_id.name,
                                                "order_id": purchase_order.id,
                                                'product_uom': lines.product_id.uom_id.id,
                                                "date_planned": datetime.today(),
                                                "company_id": po.company_id.id

                                            })
                                            if purchase_order.picking_type_id or purchase_order.company_id:
                                                if purchase_order.company_id != purchase_order.picking_type_id.company_id:
                                                    picking_types = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('company_id','=',purchase_order.company_id.id)],limit=1)
                                                    purchase_order.picking_type_id.write({'company_id' : purchase_order.company_id.id,
                                                                                          'picking_type_id' : picking_types.id})

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if not self.delivery_picking_id.state == 'confirmed':
            raise UserError(_('Please complete the delivery process to confirm'))
        self.create_rfq()
        self.delivery_picking_id._create_rfq()
        return res

    def unlink(self):
        for order in self:
            if not order.user_has_groups('odx_delivery_customization.group_delete_records'):
                raise UserError(_('You dont have access to delete order.'))
        return super(SaleOrder, self).unlink()

    def new_orders_notify(self):
        for record in self:

            # env = request.env(user=SUPERUSER_ID, su=True)
            # admin = env.ref('base.partner_admin')
            # admin_user = self.env['res.users'].browse(SUPERUSER_ID)
            # user = request.env(user=admin_user)['res.users']
            # MailChannel = env(context=user.context_get())['mail.channel']
            # MailChannel.browse(MailChannel.channel_get([admin.id])['id']) \
            #     .message_post(
            #     body=_(
            #         "Your password is the default (admin)! If this system is exposed to untrusted users it is important to change it immediately for security reasons. I will keep nagging you about it!"),
            #     message_type='comment',
            #     subtype='mail.mt_comment'
            # )
            admin_user = self.env['res.users'].browse(SUPERUSER_ID)
            MailThread = self.env['mail.thread']
            recievers = []
            if record.company_id.msg_users_id:
                for user in record.company_id.msg_users_id:
                    recievers.append(user)
                mail_vals = {}
                notification_ids = []
                for reciever in recievers:
                    email_from = admin_user.login
                    subject = 'New Orders has been placed!'
                    message = """
                                                        <html>
                                                            <head>
                                                                Dear %s,
                                                            </head>
                                                            <body style="">
                                                                New order (<a role="button" href=# data-oe-model=sale.order data-oe-id=%d>%s</a>) placed.</br>
                                                                <strong>Order Details</strong></br>
                                                                Date: %s</br>
                                                                Customer name: %s</br>
                                                                Mobile Number: %s</br></br>
                                                                Requestor : %s.<br/>
                                                                <strong>Thank You</strong>
                                                            </body>
                                                        <html>""" % (reciever.name,record.id,record.name,record.order_placed_date,record.partner_id.name,record.partner_id.mobile,admin_user.name)
                    mail_message = MailThread.message_notify(body='<pre>%s</pre>' % message,
                                                             subject='New Orders has been placed!',
                                                             subtype='mail.mt_comment',
                                                             partner_ids=(reciever.partner_id).ids,
                                                             email_from=admin_user.login)
                    notif_create_values = [{
                        'mail_message_id': mail_message.id,
                        'res_partner_id': reciever.partner_id.id,
                        'notification_type': 'inbox',
                        'notification_status': 'sent',
                    }]
                    if notif_create_values:
                        self.env['mail.notification'].sudo().create(notif_create_values)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ordered_qty = fields.Integer(string="Ordered Qty")
    product_set_uom = fields.Char(string="Selected Product UoM")
    cost = fields.Float(string="COST", compute="_check_product_cost")
    total_orderd_compute_qty = fields.Float(string="TOTAL ORDERED QTY", compute="_total_ordered_qty")
    app_ordered_qty = fields.Char(string="ORDERED QUANTITY", compute="_ordered_qty")
    initial_order_qty = fields.Float(string="Initial Quantity")


    def _total_ordered_qty(self):

        for record in self:

            today = datetime.now()
            date_today = today.date()
            # print(record.order_id)

            if record.order_id and record.order_id.date_order:
                date_created = str(record.order_id.date_order)
                create_date_split = date_created.split('.')

                created_date = datetime.strptime(create_date_split[0], '%Y-%m-%d %H:%M:%S')
                creatd_date = created_date.date()
                if creatd_date < date_today:
                    actual_qty = 1
                    if record.product_set_uom:

                        display_qty = record.product_set_uom.split(',')
                        if display_qty:
                            actual_qty_lst = display_qty[0].split(' ')
                            if actual_qty_lst:
                                actual_qty = float(actual_qty_lst[0])

                    record.update({'total_orderd_compute_qty': record.product_uom_qty * actual_qty})
                else:
                    record.total_orderd_compute_qty = record.product_uom_qty


    @api.model
    def create(self, vals):
        vals['initial_order_qty'] = vals.get('product_uom_qty')
        result = super(SaleOrderLine, self).create(vals)
        result.initial_order_qty = result.product_uom_qty
        return result


    # def write(self, values):
    #     result = super(SaleOrderLine, self).write(values)
    #     if 'product_uom_qty' in values:
    #         for line in self:
    #             line.write({'initial_order_qty': line.product_uom_qty})
    #     return result

    @api.depends('product_set_uom', 'product_uom_qty')
    def _ordered_qty(self):
        for record in self:
            if record.product_set_uom:
                display_qty = record.product_set_uom.split(',')
                ordred_qty = display_qty[0]
                qty = record.ordered_qty
                record.app_ordered_qty = str(qty) + ' ' + '*' + ' ' + str(ordred_qty)
            else:

                qty = record.product_uom_qty
                ordered_qty = str(1)
                record.app_ordered_qty = ordered_qty + ' ' + '*' + ' ' + str(qty) + str(record.product_uom.name)

    @api.depends('product_id')
    def _check_product_cost(self):
        for record in self:
            record.cost = record.product_id.standard_price

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        other_lines = self.filtered(lambda line: line.product_id.own_product == True)
        return super(SaleOrderLine, other_lines)._action_launch_stock_rule(previous_product_uom_qty)

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        for line in self:
            sale_price = 0
            unit_price = 0
            if line.product_id.own_product:
                unit_price = line.price_unit


            else:
                if line.product_uom and line.product_id:
                    price_rate = line.product_id.uom_id._compute_price(line.cost, line.product_uom)
                    line_cost_price = price_rate * line.product_uom_qty
                    cost_price = round(line_cost_price, 2)
                    # to avoid negative while takng unit price
                    price_unit = line.price_unit * line.product_uom_qty
                    # margin is taking for invoice price unit
                    sale_price = price_unit - cost_price
                    if line.product_uom_qty != 0:
                        unit_price = sale_price / line.product_uom_qty


            res.update({

                'price_unit': unit_price,
                'quantity': line.product_uom_qty,
                'product_uom_id': line.product_uom.id


            })
            if line.product_id.type == 'service':
                res.update({
                    'price_unit': line.price_unit,
                    'quantity': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_uom_id': line.product_uom.id
                })
        return res
