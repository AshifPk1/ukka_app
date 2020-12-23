# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    account_id = fields.Many2one(related='company_id.account_id',string="Expense Account")

    journal_id = fields.Many2one(related='company_id.journal_id',string="Journal")

    latest_app_version = fields.Char('Version')

    def set_values(self):
         res = super(ResConfigSettings, self).set_values()
         # self.env['ir.config_parameter'].set_param('odx_delivery_customization.account_id', self.account_id.id)
         # self.env['ir.config_parameter'].set_param('odx_delivery_customization.journal_id', self.journal_id.id)
         self.env['ir.config_parameter'].set_param('odx_delivery_customization.latest_app_version', self.latest_app_version)

         return  res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        account_details = self.env['ir.config_parameter'].sudo()
        # acounts_id = account_details.get_param('odx_delivery_customization.account_id')
        # journal_id = account_details.get_param('odx_delivery_customization.journal_id')
        latest_app_version = account_details.get_param('odx_delivery_customization.latest_app_version')



        res.update(
            # account_id = int(acounts_id),
            # journal_id = int(journal_id),
        latest_app_version = latest_app_version
        )
        return res



