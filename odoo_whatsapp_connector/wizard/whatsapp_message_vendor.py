# See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, sql_db, _
import threading
import requests
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)

import html2text


class ConvertHtmlText(object):

    def convert_html_to_text(result_txt):
        capt = b'%s' % (result_txt)
        convert_byte_to_str = capt.decode('utf-8')
        return html2text.html2text(convert_byte_to_str)


class WhatsappMessageVendor(models.TransientModel):
    _name = 'whatsapp.message.vendor'

    partner_id = fields.Many2one('res.partner', 'Vendor')
    partner_ids = fields.Many2many('res.partner', string='Contacts')
    message = fields.Text(compute='_compute_message')
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')

    @api.depends('partner_id')
    def _compute_message(self):
        for rec in self:
            order_line = []
            message = 'hii'
            if rec.partner_id:
                if rec.sale_order_id.order_line:
                    for line in rec.sale_order_id.order_line:
                        if line.product_id.seller_ids and not line.display_type == 'line_section':
                            if line.product_id.seller_ids[0].name == rec.partner_id:
                                order_line.append(line)

                result_txt = request.env['ir.ui.view'].render_template("odoo_whatsapp_connector.product_data_template",
                                                                       {
                                                                           'doc_model': 'sale.order',
                                                                           'docs': rec.sale_order_id,
                                                                           'order_line': order_line
                                                                       })
                message_txt = ConvertHtmlText.convert_html_to_text(result_txt)
                template_id = self.env['whatsapp.default'].sudo().search(
                    [('active', '=', True), ('category', '=', 'suplier')], limit=1)
                if template_id:
                    message = template_id.default_messege
                    if message:
                        message = message.replace("{{name}}", rec.partner_id.name)
                        message = message.replace("{{product_details}}", message_txt)
                        message = message.replace("{{number}}", self.sale_order_id.name)

            rec.message = message

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_ids:
            return {'domain': {'partner_id': [('id', 'in', self.partner_ids.ids)]}}
        else:
            return {'domain': {'partner_id': [('id', 'in', [])]}}

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
