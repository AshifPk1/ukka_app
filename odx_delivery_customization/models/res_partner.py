# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_delivery = fields.Boolean("Is Delivery")
    charge_per_km = fields.Float(string="Charge Per KM", domain=[('is_delivery', '=', True)])
    fixed_amount = fields.Float(string="Fixed Amount", domain=[('is_delivery', '=', True)])
    outside_purchase = fields.Boolean(string="Outside Purchase")
    is_off_duty = fields.Boolean("Off Duty",default=True)
    selected_address = fields.Boolean(string="Selected Address")
    location_link = fields.Char(string="Location")

    def name_get(self):
        """adding sequence to the name"""
        result = []
        for r in self:
            if r.mobile:
                result.append((r.id, u"%s-%s" % (r.name, r.mobile)))

            else:
                result.append((r.id, u"%s" % (r.name)))
        # print(result,"resultttt")
        return result