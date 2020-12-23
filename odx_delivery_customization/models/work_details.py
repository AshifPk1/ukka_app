from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime


class WorkDetails(models.Model):
    _name = 'work.details'

    picking_boy_id = fields.Many2one(comodel_name='res.partner', string="Picking/Delivery Boy",
                                     domain=[('is_delivery', '=', True),('is_off_duty', '=', True)], required="True",copy=False,default=lambda self: self.env.user.partner_id.id)

    starting_km = fields.Binary(string="Image of Starting KM",
                                help="Please Upload the Image Of KM Shown in Vehicle",
                                )
    starting_km_in_numbers = fields.Integer(string="Starting KM", required =True)
    ending_km = fields.Binary(string="Image of Ending KM", help="Please Upload the Image Of KM Shown in Vehicle",
                              )
    ending_km_in_numbers = fields.Integer(string="Ending KM",required =True)
    starting_time = fields.Datetime(string="Time of Start", readonly=True)
    ending_time = fields.Datetime(string="Time of Closing", readonly=True)
    total_km = fields.Integer(string="Total KM", readonly=True, compute='_compute_total_km', help="Total KM")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    state = fields.Selection([
        ('draft', 'Start'),
        ('done', 'On Duty'),
        ('closed', 'Closed')],
        string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)
    name = fields.Char(copy=False)
    picking_ids = fields.One2many('delivery.picking', 'pick_up_boy_id', string="Picking Details",
                                  domain=[('state', '=', 'pending')])
    delivery_ids = fields.One2many('delivery.picking', 'delivery_boys_id', string="Delivery Details",
                                   )
    invoice_created = fields.Boolean(string="Invoice Created")
    expense_created = fields.Boolean(string="Expense Created")


    def name_get(self):
        result = []
        for record in self:
            date = record.create_date.strftime('%Y-%m-%d')
            if record.picking_boy_id:
                name = record.picking_boy_id.name + '-' + record.name + '-' + date
                result.append((record.id, name))

        return result


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'work.details') or _('New')

        return super(WorkDetails, self).create(vals)

    def action_start(self):
        for record in self:
            # if not record.starting_km:
            #     raise UserError(_('Please provide the image of starting KM reading shown in your vehicle'))
            if not record.starting_km_in_numbers:
                raise UserError(_('Please specify the starting KM'))
            record.starting_time = datetime.datetime.now()
            record.state = 'done'
            record.picking_boy_id.is_off_duty = False

    def action_close(self):
        for record in self:
            # if not record.ending_km:
            #     raise UserError(_('Please provide the image of ending KM reading shown in your vehicle'))
            if not record.ending_km_in_numbers:
                raise UserError(_('Please specify the ending KM'))
            record.ending_time = datetime.datetime.now()
            record.state = 'closed'
            record.picking_boy_id.is_off_duty = True


    def _compute_total_km(self):
        for record in self:
            record.total_km = record.ending_km_in_numbers - record.starting_km_in_numbers

    def view_pickup_orders(self):
        for record in self:

            ctx = {'state': 'pending'}
            return {
                'name': 'PickUp Orders',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'delivery.picking',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'domain': [('pick_up_boy_id', '=', record.id), ('state', '=', 'pending')],

            }

    def view_delivery_orders(self):
        for record in self:
            ctx = {'state': 'ready'}
            return {
                'name': 'Delivery Orders',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'delivery.picking',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'domain': [('delivery_boys_id', '=', record.id), ('state', '=', 'confirmed')],

            }
