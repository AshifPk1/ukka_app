# See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, sql_db, _
import threading

import logging

_logger = logging.getLogger(__name__)


class WhatsappMessageCustomer(models.TransientModel):

    _name = 'whatsapp.message.customer'

    partner_id = fields.Many2one('res.partner', string='Contacts')
    message = fields.Text()
    sale_order_id = fields.Many2one('sale.order','Sale Order')


    def send_whatsapp_message(self):
        msg_data = []
        res = {
            'partner': self.partner_id,
            'message': self.message
        }
        msg_data.append(res)
        thread_start = threading.Thread(
            target=self.sale_order_id.send_whatsapp_message_new(msg_data))
        thread_start.start()
