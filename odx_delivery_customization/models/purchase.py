from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    purchase_payments_ids = fields.One2many('purchase.order.payments', 'purchase_id', string="Payments",
                                            )
    state = fields.Selection(selection_add=[('settled', 'Settled')])
    # sale_ref = fields.Char("Sale Order Reference", compute='sale_references')
    sale_ref = fields.Char("Sale Order Reference")

    def action_paid_status(self):
        for record in self:
            record.state = 'settled'
    #
    # def get_sale_orders(self):
    #     for line in self.order_line:
    #         print(line.sale_line_id.order_id.name,"saleeeeee")
    #         # sale_refs = []
    #         # if not line.sale_order_id.name in sale_refs:
    #         #
    #         #     sale_refs.append(line.sale_order_id.name)
    #         #     print(sale_refs,"sale_refsssssss")
    #         #     return  sale_refs
    #         # sale_refs = [ref for ref in set(line.mapped('sale_line_id.order_id.name')) if ref]
    #         # if self.sale_ref:
    #         #     return [ref for ref in self.sale_ref.split(', ') if ref and ref not in sale_refs] + sale_refs
    #         # return sale_refs
    #
    # def sale_references(self):
    #     refs = self.get_sale_orders()
    #     # self.sale_ref = ', '.join(list(refs))


class PurchaseOrderPayments(models.Model):
    _name = "purchase.order.payments"
    _description = "Purchase Order Payments"

    purchase_id = fields.Many2one(comodel_name="purchase.order", string="Purchase Order")
    date = fields.Date(string="Date")
    name = fields.Char(string="Description")
    amount = fields.Float(string="Amount")
