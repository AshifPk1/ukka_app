from calendar import monthrange
from datetime import date, datetime

from odoo import models, fields


class VendorReportWiz(models.TransientModel):
    _name = 'vendor.report.wiz'

    def _get_from_dates(self):
        date_today = fields.Date.from_string(fields.Date.context_today(self))
        return date_today.replace(day=1)

    def _get_to_dates(self):
        current_year = datetime.now().year
        current_month = datetime.now().month
        mdays = monthrange(current_year, current_month)[1]
        return date(current_year, current_month, mdays)

    date_from = fields.Date(string="Start Date", required=True, default=_get_from_dates)
    date_to = fields.Date(string="End Date", required=True, default=_get_to_dates)
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    branch_id = fields.Many2one('res.company', string="Branch")

    def get_data(self):
        return self.env.ref('odx_ukka_reports.vendor_report').report_action(self)
