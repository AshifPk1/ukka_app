from calendar import monthrange
from datetime import datetime, date

from odoo import models, fields


class DeliveryReport(models.TransientModel):
    _name = 'delivery.report.wiz'

    def _get_from_dates(self):
        date_today = fields.Date.from_string(fields.Date.context_today(self))
        return date_today.replace(day=1)

    def _get_to_dates(self):
        current_year = datetime.now().year
        current_month = datetime.now().month
        mdays = monthrange(current_year, current_month)[1]
        return date(current_year, current_month, mdays)

    date_from = fields.Date('From', default=_get_from_dates)
    date_to = fields.Date('To', default=_get_to_dates)
    branch_id = fields.Many2one('res.company', string="Branch")

    def get_data(self):
        return self.env.ref('odx_ukka_reports.delivery_report').report_action(self)