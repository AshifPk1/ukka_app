from odoo import models, fields, api, _
from odoo.exceptions import UserError
import ast


class SettlementDetails(models.Model):
    _name = 'settlement.details'
    _description = 'Details regarding the payment settlement of each delivery/picking employee'

    delivery_boys_id = fields.Many2one(comodel_name='work.details', string="Delivery Boy",copy=False)
    delivery_boy_id = fields.Many2one(comodel_name='res.partner', string="Delivery Boy",
                                      domain=[('is_delivery', '=', True)])
    # work_details_ids = fields.Many2many(comodel_name='work.details', string="Work Details")
    work_details_id = fields.Many2one(comodel_name="work.details", string="Work Details",required = True,copy=False)
    # delivery_picking_ids = fields.One2many('delivery.picking','settlement_id',string="PickUp Orders")

    charge_per_km = fields.Float("Charge Per KM", readonly=True, force_save=True)
    fixed_amount = fields.Float("Fixed Amount", readonly=True, force_save=True)
    starting_km_in_numbers = fields.Integer(related='work_details_id.starting_km_in_numbers',string="Starting KM")
    ending_km_in_numbers = fields.Integer(related='work_details_id.ending_km_in_numbers',string="Ending KM")
    total_charge_to_pay = fields.Float(string="Cash On Hand", compute='_total_amount_pay')
    total_km = fields.Integer(string="Total KM Charge", readonly=True, compute='_total_amount_pay', help="Total KM")
    name = fields.Char(string="Settlement Reference",copy=False)
    outside_purchase_cost = fields.Float(string="Outside Purchase", compute='_total_outside_cost',default=0)
    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoices")
    upi_payments = fields.Float(string="UPI Payments",compute='_total_payments')
    cash_payments = fields.Float(string="CASH Payments", compute='_total_payments')
    total_order_value = fields.Float(string="Total Orders Amount", compute='_total_amount_pay')
    payment_method_id = fields.Many2one(comodel_name='account.journal',string="Payment Method", domain=[('type', 'in', ('bank', 'cash'))])
    expense_journal_ids = fields.Many2one(comodel_name='account.move',string="To Credit")
    payment_journal_ids = fields.Many2one(comodel_name='account.move',string="Credited")
    total_credit_amount = fields.Float(string="Total Credit Amount",compute="_total_amount_pay")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('settled', 'Expense Credited'),
        ('paid','Paid')
    ],
        string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)

    @api.onchange('invoice_id')
    def working_details(self):
        return {'domain': {'work_details_id': [('invoice_created', '=', False),('expense_created','=',False),('state','=','closed')],
                           }
                }

    @api.onchange('payment_method_id')
    def journal_details(self):
        return {'domain': {'payment_method_id': [('type', 'in', ('bank', 'cash'))]
                           }
                }
    def action_confirm_settlement(self):
        self.state='settled'
        # get_param = self.env['ir.config_parameter'].sudo().get_param
        # account = get_param('odx_delivery_customization.account_id')
        account_id = self.company_id.account_id
        journal_id = self.company_id.journal_id

        # journal = get_param('odx_delivery_customization.journal_id')
        if not account_id:
            raise UserError(_("Please configure accounts in settings."))
        # account = ast.literal_eval(account)
        # journal = ast.literal_eval(journal)
        # account_id = self.env["account.account"].browse(account)
        # journal_id = self.env["account.journal"].browse(journal)
        payable_id = self.env["account.account"].search(
            [('user_type_id.id', '=', self.env.ref('account.data_account_type_payable').id)], limit=1)
        journal_entry_id = self.env['account.move'].create({
            'type': 'entry',
            'ref': self.name,
            'partner_id': self.work_details_id.picking_boy_id.id,
            'date': self.create_date,
            'journal_id': journal_id.id,

            'line_ids': [
                (0, 0, {
                    'name': self.name,
                    'account_id': account_id.id,
                    'partner_id': self.work_details_id.picking_boy_id.id,
                    'debit': self.total_km,

                }),
                (0, 0, {
                    'name': self.name,
                    'account_id': payable_id.id,
                    'partner_id': self.work_details_id.picking_boy_id.id,
                    'credit': self.total_km,

                }),




            ]
        })
        self.expense_journal_ids = journal_entry_id.id
        self.work_details_id.expense_created = True

        self.expense_journal_ids.post()



    def action_payment_settlement(self):
        self.state = 'paid'
        self.create_settlement_invoice()


    def create_settlement_invoice(self):
        """ Create settlement invoices """

        self.work_details_id.invoice_created = False

        invoice_ids = self.env['account.move'].with_context(default_type='out_invoice').create({
            'partner_id': self.work_details_id.picking_boy_id.id,
            'invoice_date': self.create_date,
            'ref': self.name,
            'amount_total': self.total_charge_to_pay,
            'invoice_line_ids': [
                (0, 0, {
                    'name': self.name,
                    'price_unit': self.total_charge_to_pay,

                }),
            ],
        })
        self.invoice_id = invoice_ids.id
        self.work_details_id.invoice_created = True

        # get_param = self.env['ir.config_parameter'].sudo().get_param
        # account = get_param('odx_delivery_customization.account_id')
        # journal = get_param('odx_delivery_customization.journal_id')
        account_id = self.company_id.account_id
        journal_id = self.company_id.journal_id
        if not account_id:
            raise UserError(_("Please configure a accounts in settings."))
        if not self.payment_method_id:
            raise UserError(_("Please select a payment method."))
        # account = ast.literal_eval(account)
        # account_id = self.env["account.account"].search([('id', '=', account)], limit=1)
        payable_id = self.env["account.account"].search(
            [('user_type_id.id', '=', self.env.ref('account.data_account_type_payable').id)], limit=1)
        # journal_id = self.env["account.journal"].search([('id', '=', journal)], limit=1)


        journal_entry_ids = self.env['account.move'].create({
            'type': 'entry',
            'ref': self.name,
            'partner_id':self.work_details_id.picking_boy_id.id,
            'journal_id':journal_id.id,
            'date': self.create_date,
            'line_ids': [

                (0, 0, {
                    'name': self.name,
                    'account_id': self.payment_method_id.default_credit_account_id.id,
                    'partner_id': self.work_details_id.picking_boy_id.id,
                    'credit': self.total_km,

                }),
                (0, 0, {
                    'name': self.name,
                    'account_id': payable_id.id,
                    'partner_id': self.work_details_id.picking_boy_id.id,
                    'debit': self.total_km,

                })


            ]
        })
        self.payment_journal_ids = journal_entry_ids.id
        self.expense_payment_reconcile()


    def expense_payment_reconcile(self):

       expense_lines = []

       if self.expense_journal_ids:
            # self.expense_journal_ids.post()
            if self.expense_journal_ids.state == 'posted':
                for line in self.expense_journal_ids.line_ids:
                    expense_lines.append(line)

       payment_lines = []
       if self.payment_journal_ids:

            self.payment_journal_ids.post()
            if self.payment_journal_ids.state == 'posted':
                for line in self.payment_journal_ids.line_ids:
                     payment_lines.append(line)


            expense_lines += payment_lines

        #
            account_move_lines_to_reconcile = self.env['account.move.line']
            for line in expense_lines:

                if line.account_id.internal_type == 'payable':
                    account_move_lines_to_reconcile |= line
                account_move_lines_to_reconcile.filtered(lambda l: l.reconciled == False).reconcile()



    def view_settlement_invoice(self):

        for record in self:
            return {
                'name': 'Settlement Invoice',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': record.invoice_id.id,
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',

            }
    def view_to_pay_journals(self):
        for record in self:
            return {
                'name': 'Journals To Credit',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': record.expense_journal_ids.id,
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }
    def view_paid_journals(self):
        for record in self:
            return {
                'name': 'Credited Journals',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': record.payment_journal_ids.id,
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'settlement.details') or _('New')

        return super(SettlementDetails, self).create(vals)

    @api.onchange('work_details_id')
    def on_change_work_details(self):
        if self.work_details_id:
            # self.starting_km_in_numbers = self.work_details_id.starting_km_in_numbers
            # self.ending_km_in_numbers = self.work_details_id.ending_km_in_numbers
            self.charge_per_km = self.work_details_id.picking_boy_id.charge_per_km
            self.fixed_amount = self.work_details_id.picking_boy_id.fixed_amount

    @api.depends('work_details_id')
    def _total_payments(self):
        for record in self:
            record.upi_payments = 0
            record.cash_payments= 0
            if record.work_details_id.delivery_ids:
                for line in record.work_details_id.delivery_ids:
                    if line.payment_method_id.type == 'bank':
                        record.upi_payments = record.upi_payments + line.total_collected_amount
                    if line.payment_method_id.type == 'cash':
                        record.cash_payments = record.cash_payments + line.total_collected_amount

    @api.depends('work_details_id')
    def _total_outside_cost(self):

        for record in self:
            pick_up_ids = self.env['delivery.picking'].search([('pick_up_boy_id', '=', record.work_details_id.id)])
            record.outside_purchase_cost = 0

            for pick_up in pick_up_ids:
                if pick_up.picking_lines_ids:
                    for line in pick_up.picking_lines_ids:
                        record.outside_purchase_cost = record.outside_purchase_cost + line.cost * line.product_qty




    @api.depends('work_details_id')
    def _total_amount_pay(self):
        for record in self:
            record.total_km = record.work_details_id.total_km * record.charge_per_km
            total_payments = 0
            credit_amount_total =0
            record.total_charge_to_pay =0
            if record.work_details_id.delivery_ids:
                for line in record.work_details_id.delivery_ids:
                    total_payments    = total_payments + line.total_collected_amount
                    if line.payment_status == 'credit':
                        credit_amount_total = credit_amount_total + line.total_collected_amount
                record.total_order_value = total_payments
                record.total_credit_amount = credit_amount_total

            record.total_charge_to_pay = record.total_order_value -record.total_credit_amount - record.upi_payments - record.outside_purchase_cost


