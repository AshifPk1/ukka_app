from odoo import fields, models, api, _
from datetime import datetime
from datetime import date


class DeliveryPicking(models.Model):
    _name = 'delivery.time.slot'
    _description = 'Select time slot for scheduled delivery'

    from_time = fields.Float(string="From Time", required=True)
    to_time = fields.Float(string="To Time", required=True)
    name = fields.Char(string="Name",compute="_time_slot")
    timing = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM'),
    ],
        string='AM/PM',
        default='am'
    )

    def name_get(self):
        result = []
        for record in self:

            if record.from_time and record.to_time:
                name = str(record.from_time) + '-' + str(record.to_time)
                result.append((record.id, name))

        return result
    @api.depends('from_time','to_time')
    def _time_slot(self):
        for record in self:
            record.name = str(record.from_time) + '-' + str(record.to_time)