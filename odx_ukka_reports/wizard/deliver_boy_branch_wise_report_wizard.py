# -*- coding: utf-8 -*-
from calendar import monthrange
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import models, api, fields, _


class DeliveryBoyStoreWiz(models.TransientModel):
    _name = "delivery.boy.report.xlsx.wiz"

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
    deliver_boy = fields.Many2one('res.partner',string="Deliver Boy")
    branch_id = fields.Many2one('res.company',string="Branch")




    def print_report_xlsx(self):
        data = {'date_from': self.date_from,
                'date_to': self.date_to,
                'wiz_id': self.id}
        return self.env.ref('odx_ukka_reports.deliver_boy_branch_xlsx_report').report_action(self, data=data)