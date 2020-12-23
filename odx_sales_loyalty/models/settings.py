# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    activate_loyalty = fields.Boolean(string="Sales Loyalty",default=False)
    loyalty_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program',
                                 help='The loyalty program used by this point of sale.')

    @api.onchange('activate_loyalty')
    def _onchange_activate_loyalty(self):
        if self.activate_loyalty:
            self.loyalty_id = self.env['sale.loyalty.program'].search([], limit=1)
        else:
            self.loyalty_id = False

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('odx_sales_loyalty.activate_loyalty', self.activate_loyalty)
        self.env['ir.config_parameter'].set_param('odx_sales_loyalty.loyalty_id', self.loyalty_id.id)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        loyalty_details = self.env['ir.config_parameter'].sudo()
        activate_loyalty = loyalty_details.get_param('odx_sales_loyalty.activate_loyalty')
        loyalty_id = loyalty_details.get_param('odx_sales_loyalty.loyalty_id')

        res.update(
            activate_loyalty=activate_loyalty,
            loyalty_id=int(loyalty_id)
        )
        return res

