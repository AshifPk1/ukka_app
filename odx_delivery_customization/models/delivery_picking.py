# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import fields, models, api, _


class DeliveryPicking(models.Model):
    _name = 'delivery.picking'

    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Manage Delivery as well as Picking Details'

    # picking details
    name = fields.Char(string="Deliver Reference", copy=False)
    pick_up_boy_id = fields.Many2one(comodel_name='work.details', string="Picking Boy", copy=False)
    delivery_boys_id = fields.Many2one(comodel_name='work.details', string="Delivery Boy", copy=False)

    sale_order_id = fields.Many2one(comodel_name='sale.order', string="Sale Order", copy=False)
    picking_boy_id = fields.Many2one(comodel_name='res.partner', string="Picking Boy",
                                     domain=[('is_delivery', '=', True)])
    delivery_boy_id = fields.Many2one(comodel_name='res.partner', string="Delivery Boy",
                                      domain=[('is_delivery', '=', True)])

    create_time = fields.Datetime(string='Created On', required=True, default=fields.Datetime.now,
                                  help="Creation date of picking/delivery orders,\nConfirmation date of confirmed orders.")

    picking_lines_ids = fields.One2many('delivery.picking.line', 'picking_line_id', string="Picking Details",
                                        store=True)
    delivery_lines_ids = fields.One2many('delivery.picking.line', 'delivery_line_id', string="Delivery Details")
    total_ordered_amount = fields.Float(string="Total Order Amount", readonly=True)
    total_returned_amount = fields.Float(string="Returned Amount", readonly=True, compute='_compute_totals')
    total_collected_amount = fields.Float(string="Total Collected Amount", readonly=True, compute='_compute_totals')
    address = fields.Char(string="Address")
    mobile_number = fields.Char(string="Mobile Number", related="sale_order_id.partner_shipping_id.mobile")
    street = fields.Char(string="Street")
    city = fields.Char(string="City")
    customer_name = fields.Char(string="Customer")
    location_link = fields.Char(string="Location", store=True)
    zip = fields.Char(string="ZIP")
    state_id = fields.Many2one(comodel_name="res.country.state", string="State",
                               related="sale_order_id.partner_id.state_id")

    state = fields.Selection([
        ('pending', 'Ready for PickUp'),
        ('ready', 'Ready To Deliver'),
        ('confirmed', 'Delivered')],
        string='Status', index=True, readonly=True, default='pending',
        track_visibility='onchange', copy=False)
    settlement_id = fields.Many2one(comodel_name='settlement.details', string="Settlement Details", copy=False)
    payment_id = fields.Many2one(comodel_name='account.payment', string="Payment Details")
    payment_status = fields.Selection([
        ('paid', 'Paid'),
        ('credit', 'Credit'),
    ],
        string='Payment Status',
        default='paid'
    )
    payment_method_id = fields.Many2one(comodel_name='account.journal', string='Payment Methods',
                                        domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    picking_user_id = fields.Many2one('res.users', 'Picked By')
    picking_time = fields.Datetime("Picking On")
    delivery_user_id = fields.Many2one('res.users', 'Delivered By')
    delivered_time = fields.Datetime("Delivered On")
    picking_partner_id = fields.Many2one(comodel_name='res.partner', string="Ordered Customer")
    delivery_charges = fields.Float(string='Delivery Charges')
    discount = fields.Float(string='Discount')
    time_for_picking = fields.Char(string="Time for Picking",compute='_time_for_picking')
    time_for_delivery = fields.Char(string="Time for Delivery",compute='_time_for_delivery')

    # @api.depends('payment_method_id')
    # def journal_details(self):
    #     return {'domain': {'payment_method_id': [('type', 'in', ('bank', 'cash'))],
    #                        }
    #             }
    urgent_shipping = fields.Boolean(string="Urgent shipping", compute="_check_urgent_boolean")

    def _time_for_picking(self):
        for record in self:
            difference = relativedelta(hours=0, minutes=0, seconds=0)
            d1 = fields.Datetime.from_string(record.picking_time)
            d2 = fields.Datetime.from_string(record.create_time)
            difference = difference + relativedelta(d1, d2)
            if difference.days:
                hrs = 24 * difference.days

                qut_pick_avg_time = str(hrs) + ':' + str(difference.minutes) + ':' + str(
                    difference.seconds) + ' - Hours'
                record.time_for_picking = qut_pick_avg_time
            elif difference.hours:
                qut_pick_avg_time = str(difference.hours) + ':' + str(difference.minutes) + ':' + str(
                    difference.seconds) + ' - Hours'
                record.time_for_picking = qut_pick_avg_time
            elif difference.minutes:
                qut_pick_avg_time = str(difference.hours) + ':' + str(difference.minutes) + ':' + str(
                    difference.seconds) + ' - Minutes'
                record.time_for_picking = qut_pick_avg_time
            else:
                qut_pick_avg_time = str(difference.hours) + ':' + str(difference.minutes) + ':' + str(
                    difference.seconds) + ' - Seconds'
                record.time_for_picking = qut_pick_avg_time

    def _time_for_delivery(self):
        for record in self:
            difference = relativedelta(hours=0, minutes=0, seconds=0)
            d1 = fields.Datetime.from_string(record.delivered_time)
            d2 = fields.Datetime.from_string(record.picking_time)
            difference = difference + relativedelta(d1, d2)
            if difference.days:
                hrs = 24 * difference.days
                qut_pick_avg_time = str(hrs) + ':' + str(difference.minutes) + ':' + str(
                    difference.seconds) + ' - Hours'
                record.time_for_delivery = qut_pick_avg_time
            elif difference.hours:
                qut_pick_avg_time = str(difference.hours) + ':' + str(difference.minutes) + ':' + str(
                    difference.seconds) + ' - Hours'
                record.time_for_delivery = qut_pick_avg_time
            elif difference.minutes:
                qut_pick_avg_time = str(difference.hours) + ':' + str(difference.minutes) + ':' + str(
                    difference.seconds) + ' - Minutes'
                record.time_for_delivery = qut_pick_avg_time
            else:
                qut_pick_avg_time = str(difference.hours) + ':' + str(difference.minutes) + ':' + str(
                    difference.seconds) + ' - Seconds'
                record.time_for_delivery = qut_pick_avg_time


    def edit_delivered_order(self):
        for record in self:
            if record.state == 'confirmed':
                record.write({'state': 'ready'})

    def edit_picked_order(self):
        for record in self:
            if record.state == 'ready':
                record.write({'state': 'pending'})

    @api.depends('sale_order_id')
    def _check_urgent_boolean(self):
        for record in self:
            if record.sale_order_id.shipping_urgent:
                record.urgent_shipping = True
            else:
                record.urgent_shipping = False

    @api.onchange('pick_up_boy_id', 'delivery_boys_id')
    def working_boys_now(self):
        today = date.today()
        check_date_end = str(today) + ' ' + '23:59:59'
        check_date_start = str(today) + ' ' + '00:00:00'

        return {'domain': {
            'pick_up_boy_id': [('starting_time', '<=', check_date_end), ('starting_time', '>=', check_date_start),
                               ('state', '=', 'done')],
            'delivery_boys_id': [('starting_time', '<=', check_date_end), ('starting_time', '>=', check_date_start),
                                 ('state', '=', 'done')]}
        }

    def _create_rfq(self):
        for record in self:
            purchase = ''
            purchase_order_line_obj = self.env['purchase.order.line']
            purchase_order_obj = self.env['purchase.order']
            if record.picking_lines_ids:
                for lines in record.picking_lines_ids:
                    if record.sale_order_id.order_line:
                        product_list = []
                        products = ''
                        for sale_order_line in record.sale_order_id.order_line:
                            if sale_order_line.product_id.standard_price == 0 and not sale_order_line.product_id.type == 'service':
                                if sale_order_line.product_id not in product_list:
                                    product_list.append(sale_order_line.product_id)

                        for prdt in product_list:
                            products += ' ' + prdt.name + ','
                        if products:
                            raise UserError(_('Please add cost price for the following products %s.') % (products))

                    if lines.is_outside and not lines.display_type == 'line_section':

                        po = False

                        vendors = self.env['res.partner'].search([('outside_purchase', '=', True)], limit=1)

                        if vendors:
                            po = self.env['purchase.order'].sudo().search(
                                [('state', '=', 'draft'), ('partner_id.outside_purchase', '=', True),
                                 ('partner_id', '=', vendors.id),
                                 ('company_id', '=', record.sale_order_id.company_id.id)], limit=1)

                            if po:
                                flag = False
                                source_list = []
                                if po.sale_ref:
                                    source_list = po.sale_ref.split(',')
                                for doc in source_list:
                                    if doc == record.sale_order_id.name:
                                        flag = True
                                if not flag:
                                    sale_reff = ' '
                                    if po.sale_ref and record.sale_order_id:
                                        po.write({
                                            'sale_ref': po.sale_ref + ',' + record.sale_order_id.name
                                        })
                                    else:
                                        po.write({
                                            'sale_ref': sale_reff
                                        })

                                for line in po.order_line:
                                    if line.product_id == lines.product_id:
                                        quantity = 0
                                        unit_cost = 0

                                        if lines.sale_order_line_id and lines.sale_order_line_id.product_uom and line.product_uom != lines.sale_order_line_id.product_uom:

                                            quantity = lines.sale_order_line_id.product_uom._compute_quantity(
                                                lines.sale_order_line_id.product_uom_qty,
                                                line.product_uom)

                                            line.product_qty = quantity + line.product_qty
                                        else:
                                            line.product_qty = lines.sale_order_line_id.product_uom_qty + line.product_qty
                                if not any(line.product_id == lines.product_id for line in po.order_line):
                                    quantity = 0
                                    unit_cost = 0
                                    if lines.sale_order_line_id and lines.sale_order_line_id.product_uom:
                                        quantity = lines.sale_order_line_id.product_uom._compute_quantity(
                                            lines.sale_order_line_id.product_uom_qty,
                                            lines.product_id.uom_id)
                                        unit_cost = round(lines.cost, 2) / quantity

                                    purchase_order_line = purchase_order_line_obj.create({

                                        'product_id': lines.product_id.id,
                                        'product_qty': quantity,
                                        'price_unit': unit_cost,
                                        'price_subtotal': lines.price_subtotal,
                                        'name': lines.product_id.name,
                                        "order_id": po.id,
                                        'product_uom': lines.product_id.uom_id.id,
                                        "date_planned": datetime.today(),
                                        "company_id": po.company_id.id

                                    })


                            else:


                                purchase_order = purchase_order_obj.create({
                                    "partner_id": vendors.id,
                                    "company_id": record.sale_order_id.company_id.id,
                                    "sale_ref": record.sale_order_id.name,

                                })
                                quantity = 0
                                unit_cost = 0
                                if lines.sale_order_line_id and lines.sale_order_line_id.product_uom:
                                    quantity = lines.sale_order_line_id.product_uom._compute_quantity(
                                        lines.sale_order_line_id.product_uom_qty,
                                        lines.product_id.uom_id)
                                    unit_cost = round(lines.cost, 2) / quantity

                                purchase_order_line = purchase_order_line_obj.create({

                                    'product_id': lines.product_id.id,
                                    'product_qty': quantity,
                                    'price_unit': unit_cost,
                                    'price_subtotal': lines.price_subtotal,
                                    'name': lines.product_id.name,
                                    "order_id": purchase_order.id,
                                    'product_uom': lines.product_id.uom_id.id,
                                    "date_planned": datetime.today(),
                                    "company_id": record.sale_order_id.company_id.id

                                })
                                if purchase_order.picking_type_id or purchase_order.company_id:
                                    if purchase_order.company_id != purchase_order.picking_type_id.company_id:
                                        picking_types = self.env['stock.picking.type'].search(
                                            [('code', '=', 'incoming'),
                                             ('company_id', '=', purchase_order.company_id.id)], limit=1)
                                        purchase_order.picking_type_id.write(
                                            {'company_id': purchase_order.company_id.id,
                                             'picking_type_id': picking_types.id})

    def create(self, vals):

        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'delivery.picking') or _('New')

        return super(DeliveryPicking, self).create(vals)


    def thankyou_note_message(self):
        self.sale_order_id.send_whatsapp_thankyou_note()

    def action_confirm(self):
        for record in self:
            if record.picking_lines_ids:
                for picking_line in record.picking_lines_ids:
                    if picking_line.is_outside:
                        if picking_line.cost == 0.0:
                            raise UserError(_('Please enter the cost of outside purchased product.'))

            record.write({'state': 'ready'})
            record.picking_user_id = self.env.user.id
            record.picking_time = datetime.now()
            # record._create_rfq()
            record.sale_order_id.send_whatsapp_delivery_boy()



    def action_delivered_confirm(self):
        for record in self:
            if record.payment_status == 'paid':
                if not record.payment_method_id:
                    raise UserError(_('Please select a payment method to continue!'))
            record.write({'state': 'confirmed'})
            record.delivery_user_id = self.env.user.id
            record.delivered_time = datetime.now()

            if self.sale_order_id.state in ('draft'):
                for picking_line in self.picking_lines_ids:

                    # print(picking_line,"picking_line")
                    # print(picking_line.returned_qty_uom, "do uom")
                    if picking_line.sale_order_line_id and picking_line.product_uom:

                        if picking_line.sale_order_line_id.product_id.id == picking_line.product_id.id:
                            returned_quantity = picking_line.returned_qty_uom._compute_quantity(
                                picking_line.returned_qty,
                                picking_line.sale_order_line_id.product_uom)
                            if returned_quantity > 0:
                                if not picking_line.returned_qty_uom:
                                    raise UserError(_('Please choose any uom for the quantity to be returned!'))
                            if picking_line.sale_order_line_id.initial_order_qty >= returned_quantity:
                                # returned_amount = picking_line.mrp * returned_quantity
                                # print(returned_amount,"returned_amount")
                                sale_order_qty = picking_line.sale_order_line_id.initial_order_qty
                                total_order_qty = sale_order_qty - returned_quantity

                                # print(returned_quantity,"quantityyyy")
                                picking_line.sale_order_line_id.write({
                                        'product_uom_qty': total_order_qty
                                     })

            if record.payment_status == 'paid':
                record.sale_order_id.is_paid = True
            else:
                record.sale_order_id.is_credit = True
            # record.create_payment()

    @api.depends('picking_lines_ids')
    def _compute_totals(self):
        for record in self:
            record.total_returned_amount = 0
            record.total_collected_amount = 0
            for line in record.picking_lines_ids:
                quantity = line.returned_qty_uom._compute_quantity(
                    line.returned_qty,
                    line.sale_order_line_id.product_uom)
                record.total_returned_amount = record.total_returned_amount + quantity * line.mrp

                record.total_collected_amount = record.total_ordered_amount - record.total_returned_amount

    # def create_payment(self):
    #     """ Create a register payment """
    #
    #     journals = self.env['account.journal'].search(
    #         [('type', '=', 'cash')], limit=1)
    #
    #     payment_ids = self.env['account.payment'].create({
    #         'journal_id': journals.id,
    #         'payment_type': 'inbound',
    #         'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
    #
    #         'payment_date': self.create_time,
    #         'amount': self.total_collected_amount,
    #
    #         'partner_id': self.sale_order_id.partner_id.id,
    #         'partner_type': 'customer',
    #         'communication': '%s-%s' % (self.sale_order_id.name, self.name)
    #     })
    #     payment_ids.post()
    #     self.payment_id = payment_ids.id
    #     self.sale_order_id.payment_id = payment_ids.id

    # def view_register_payment(self):
    #     for record in self:
    #         return {
    #             'name': 'Payment Details',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_id': record.payment_id.id,
    #             'res_model': 'account.payment',
    #             'view_id': False,
    #             'type': 'ir.actions.act_window',
    #
    #         }


class DeliveryPickingLine(models.Model):
    _name = 'delivery.picking.line'

    picking_line_id = fields.Many2one('delivery.picking', string='Picking')
    delivery_line_id = fields.Many2one('delivery.picking', string="Delivery")
    product_id = fields.Many2one('product.product', string="Product")
    product_qty = fields.Float(string="Total Quantity")
    price_unit = fields.Float(string="Unit Price")
    price_subtotal = fields.Float(string="SubTotal")
    is_picked = fields.Boolean(string="Picked", copy=False)
    mrp = fields.Float(string="MRP/Unit Price")
    is_outside = fields.Boolean(string="Outside Purchase", copy=False)
    cost = fields.Float(string="Cost")
    returned_qty = fields.Float(string="Returned Qty")
    name = fields.Char('Name', readonly="true")
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Detail')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    create_time = fields.Datetime(related='picking_line_id.create_time', string='Created On')
    category = fields.Many2one(comodel_name="product.category", related='product_id.categ_id', store=True)
    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor")
    product_uom = fields.Many2one(comodel_name="uom.uom", string="Uom")
    total_ordred_qty = fields.Char(string="Ordered Quantity")
    returned_qty_uom = fields.Many2one(comodel_name="uom.uom", string="Returned Qty Uom",domain="[('category_id', '=', product_uom_category_id)]",store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)


    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note'),
    ], default=False, help="Technical field for UX purpose.")
    update_order = fields.Integer(string="Updates", default=0)

    def toggle_active(self):
        for record in self:
            record.is_outside = not record.is_outside

    def toggles_active(self):
        for record in self:
            record.is_picked = not record.is_picked



    # def name_get(self):
    #     result = []
    #     for record in self:
    #
    #         if record.picking_line_id:
    #             name = record.picking_line_id.name + '-' + record.product_id.name
    #             result.append((record.id, name))
    #
    #     return result
#
#
# delivery_picking_line_id = env['delivery.picking.line'].browse(env.context['active_ids'])
# if delivery_picking_line_id:
#     for line in delivery_picking_line_id:
#         if not line.vendor_id and line.display_type != 'line_section':
#             if line.product_id.seller_ids:
#                 line.write({'vendor_id': line.product_id.seller_ids[0].name.id})
