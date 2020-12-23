# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    customer_password = fields.Char("Password")

