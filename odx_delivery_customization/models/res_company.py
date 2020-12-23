# -*- coding: utf-8 -*-

from odoo import fields, models, api, tools


class ResPartner(models.Model):
    _inherit = 'res.company'

    banner_images_ids = fields.One2many('banner.images', 'company_id', string='Attach Banner Images')
    terms_and_conditions = fields.Html(string='Terms and Conditions')
    upi_id = fields.Char("UPI ID")
    person_name = fields.Char("Name")
    mechant_id = fields.Char("Merchant ID")
    account_id = fields.Many2one(comodel_name='account.account', string="Expense Account")
    journal_id = fields.Many2one(comodel_name='account.journal', string="Journal")
    msg_users_id = fields.Many2many('res.users', string='Message Users')


