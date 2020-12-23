from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one('sale.order', string="Sale Details", copy=False)

    # def invoice_payment_reconcile(self):
    #
    #     for record in self:
    #
    #         invoice_lines = []
    #         if record.state == 'posted':
    #             for inv in record.line_ids:
    #                 invoice_lines.append(inv)
    #
    #         payment_lines = []
    #         if record.sale_id:
    #             payments = record.sale_id.payment_id.move_line_ids.move_id.line_ids
    #
    #             for pay in payments:
    #                 payment_lines.append(pay)
    #
    #         invoice_lines += payment_lines
    #
    #         account_move_lines_to_reconcile = self.env['account.move.line']
    #         for line in invoice_lines:
    #
    #             if line.account_id.internal_type == 'receivable':
    #                 account_move_lines_to_reconcile |= line
    #             account_move_lines_to_reconcile.filtered(lambda l: l.reconciled == False).reconcile()
    #
    # def post(self):
    #
    #     res = super(AccountMove, self).post()
    #     self.invoice_payment_reconcile()
    #     return res
