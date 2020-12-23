from odoo import models, fields, api, _


class ShippingMethod(models.Model):
    _inherit = 'delivery.carrier'

    scheduled_delivery = fields.Boolean("Scheduled Delivery")
    delivery_time = fields.Char("Delivery Time")
    urgent_delivery = fields.Boolean("Urgent Delivery")