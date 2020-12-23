from odoo import models, fields, api,sql_db, _
from odoo.exceptions import UserError
from datetime import date
import requests
import json
from datetime import datetime
import time
import threading
from odoo.http import request
import html2text

class ConvertHtmlText(object):

    def convert_html_to_text(result_txt):
        capt = b'%s' % (result_txt)
        convert_byte_to_str = capt.decode('utf-8')
        return html2text.html2text(convert_byte_to_str)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def send_whatsapp_mesage(self):
        msg_data = []
        company_id = self.env.user and \
                     self.env.user.company_id or False
        if company_id and not company_id.authenticate:
            raise UserError(_('Whatsapp Authentication Failed.'
                              ' Configure Whatsapp Configuration'
                              ' in company setting.'))
        company_id.check_auth()
        message = 'hii'
        result_txt = request.env['ir.ui.view'].render_template("odoo_whatsapp_connector.product_data_template", {
            'doc_model': 'sale.order',
            'docs': self,
            'order_line': self.order_line
        })
        message_txt = ConvertHtmlText.convert_html_to_text(result_txt)
        template_id = self.env['whatsapp.default'].sudo().search([('active', '=', True),('category', '=', 'customer')], limit=1)
        if template_id:
            message = template_id.default_messege
            if message:
                message = message.replace("{{name}}", self.partner_id.name)
                message = message.replace("{{product_details}}", message_txt)
                message = message.replace("{{number}}", self.name)
        res = {
            'partner':self.partner_id,
            'message':message
        }
        msg_data.append(res)

        view = self.env.ref('odoo_whatsapp_connector.whatsapp_message_customer_view')
        return {
            'name': "Whatsapp Message",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'whatsapp.message.customer',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {
                'default_message': message,
                'default_sale_order_id':self.id,
                'default_partner_id':self.partner_id.id
                # 'default_partner_ids':[self.partner_id.id]
            },
        }
    def send_whatsapp_picking_boy(self):

        msg_data = []
        company_id = self.env.user and \
                     self.env.user.company_id or False
        if company_id and not company_id.authenticate:
            raise UserError(_('Whatsapp Authentication Failed.'
                              ' Configure Whatsapp Configuration'
                              ' in company setting.'))
        company_id.check_auth()
        message = 'hii'
        result_txt = request.env['ir.ui.view'].render_template("odoo_whatsapp_connector.picking_data_template", {
            'doc_model': 'sale.order',
            'docs': self,
            'order_line': self.order_line
        })

        message_txt = ConvertHtmlText.convert_html_to_text(result_txt)
        template_id = self.env['whatsapp.default'].sudo().search([('active', '=', True), ('category', '=', 'pickup_boy')],
                                                               limit=1)

        if template_id:

            message = template_id.default_messege
            if message:
                
                message = message.replace("{{name}}", self.pick_up_boy_id.picking_boy_id.name)
                message = message.replace("{{product_details}}", message_txt)
                message = message.replace("{{number}}", self.name)
        res = {
            'partner': self.pick_up_boy_id.picking_boy_id,
            'message': message
        }
        msg_data.append(res)

        thread_start = threading.Thread(
            target=self.send_whatsapp_message_new(msg_data))
        thread_start.start()

    def send_whatsapp_delivery_boy(self):

        msg_data = []
        company_id = self.env.user and \
                     self.env.user.company_id or False
        if company_id and not company_id.authenticate:
            raise UserError(_('Whatsapp Authentication Failed.'
                              ' Configure Whatsapp Configuration'
                              ' in company setting.'))
        company_id.check_auth()
        message = 'hii'
        result_txt = request.env['ir.ui.view'].render_template("odoo_whatsapp_connector.picking_data_template", {
            'doc_model': 'sale.order',
            'docs': self,
            'order_line': self.order_line
        })
        # print(result_txt,"resultttt")
        message_txt = ConvertHtmlText.convert_html_to_text(result_txt)
        template_id = self.env['whatsapp.default'].sudo().search(
            [('active', '=', True), ('category', '=', 'delivery_boy')],
            limit=1)

        if template_id:

            message = template_id.default_messege
            if message:
                message = message.replace("{{name}}", self.delivery_boys_id.picking_boy_id.name)
                message = message.replace("{{product_details}}", message_txt)
                message = message.replace("{{number}}", self.name)
        res = {
            'partner': self.delivery_boys_id.picking_boy_id,
            'message': message
        }
        msg_data.append(res)

        thread_start = threading.Thread(
            target=self.send_whatsapp_message_new(msg_data))
        thread_start.start()



    def quick_send_whatsapp_mesage(self):
        msg_data = []
        company_id = self.env.user and \
                     self.env.user.company_id or False
        if company_id and not company_id.authenticate:
            raise UserError(_('Whatsapp Authentication Failed.'
                              ' Configure Whatsapp Configuration'
                              ' in company setting.'))
        company_id.check_auth()
        message = 'hii'
        result_txt = request.env['ir.ui.view'].render_template("odoo_whatsapp_connector.product_data_template", {
            'doc_model': 'sale.order',
            'docs': self,
            'order_line': self.order_line
        })
        message_txt = ConvertHtmlText.convert_html_to_text(result_txt)
        template_id = self.env['whatsapp.default'].sudo().search([('active', '=', True),('category', '=', 'customer')], limit=1)
        if template_id:

            message = template_id.default_messege
            if message:
                message = message.replace("{{name}}", self.partner_id.name)
                message = message.replace("{{product_details}}", message_txt)
                message = message.replace("{{number}}", self.name)
        res = {
            'partner':self.partner_id,
            'message':message
        }
        msg_data.append(res)

        thread_start = threading.Thread(
            target=self.send_whatsapp_message_new(msg_data))
        thread_start.start()

    def send_whatsapp_thankyou_note(self):
        msg_data = []
        company_id = self.env.user and \
                     self.env.user.company_id or False
        if company_id and not company_id.authenticate:
            raise UserError(_('Whatsapp Authentication Failed.'
                              ' Configure Whatsapp Configuration'
                              ' in company setting.'))
        company_id.check_auth()
        message = 'hii'
        result_txt = request.env['ir.ui.view'].render_template("odoo_whatsapp_connector.product_data_template", {
            'doc_model': 'sale.order',
            'docs': self,
            'order_line': self.order_line
        })
        message_txt = ConvertHtmlText.convert_html_to_text(result_txt)
        template_id = self.env['whatsapp.default'].sudo().search(
            [('active', '=', True), ('category', '=', 'note')], limit=1)
        if template_id:

            message = template_id.default_messege
            if message:
                message = message.replace("{{name}}", self.partner_id.name)
                message = message.replace("{{product_details}}", message_txt)
                message = message.replace("{{number}}", self.name)
        res = {
            'partner': self.partner_id,
            'message': message
        }
        msg_data.append(res)

        thread_start = threading.Thread(
            target=self.send_whatsapp_message_new(msg_data))
        thread_start.start()

    def send_whatsapp_message_new(self,msg_data):
        try:
            new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
            uid, context = self.env.uid, self.env.context
            with api.Environment.manage():
                self.env = api.Environment(new_cr, uid, context)
                company_id = self.env.user and \
                             self.env.user.company_id or False
                path = company_id and company_id.api_url + \
                       str(company_id.instance_no)
                token_value = {'token': company_id.api_token}
                url_path = path + '/sendMessage'
                for msg in msg_data:
                    whatsapp_log_obj = self.env['whatsapp.message.log']
                    message_data = {'phone': msg['partner'].mobile,
                                    'body': msg['message']}
                    data = json.dumps(message_data)

                    request_meeting = requests.post(
                        url_path, data=data, params=token_value,
                        headers={'Content-Type': 'application/json'})
                    subtype_id = self.env['mail.message.subtype'].search([('name', '=', 'Note')])
                    self.env['mail.message'].create({
                        'body': msg['message'],
                        'model': 'sale.order',
                        'message_type': 'comment',
                        'res_id': self.id,
                        'subtype_id': subtype_id.id,
                    })
                    # print(request_meeting)
                    if request_meeting.status_code == 200:
                        data = json.loads(request_meeting.text)
                        chat_id = data.get('id') and \
                                  data.get('id').split('_')
                        whatsapp_log_obj.create(
                            {'name': msg['partner'].name,
                             'msg_date': datetime.now(),
                             'link': url_path,
                             'data': data,
                             'chat_id': chat_id[1],
                             'message': request_meeting.text,
                             'message_body': msg['message'],
                             'status': 'send'})
                        msg['partner'].chat_id = chat_id[1]
                    else:
                        whatsapp_log_obj.create(
                            {'name': msg['partner'].name,
                             'msg_date': datetime.now(),
                             'link': url_path,



                             'message_body': msg['message'],
                             'status': 'error'})


                    new_cr.commit()
                    time.sleep(3)
        finally:
            self.env.cr.close()


    def send_whatsapp_to_vendor(self):
        company_id = self.env.user and \
                     self.env.user.company_id or False
        if company_id and not company_id.authenticate:
            raise UserError(_('Whatsapp Authentication Failed.'
                              ' Configure Whatsapp Configuration'
                              ' in company setting.'))
        company_id.check_auth()
        venodr_list = []
        msg_data = []
        message = 'hii'
        ids = []
        if self.order_line:
            for line in self.order_line:
                if line.product_id.seller_ids and not line.display_type == 'line_section':
                     if line.product_id.seller_ids[0].name not in venodr_list:
                        venodr_list.append(line.product_id.seller_ids[0].name)


        for venodr in venodr_list:
            ids.append(venodr.id)

        view = self.env.ref('odoo_whatsapp_connector.whatsapp_message_vendor_view')
        return {
            'name': "Whatsapp Message",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'whatsapp.message.vendor',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {
                'default_message': 'hii',
                'default_sale_order_id': self.id,
                'default_partner_ids': ids
            },
        }


    def quick_send_whatsapp_to_vendor(self):
        company_id = self.env.user and \
                     self.env.user.company_id or False
        if company_id and not company_id.authenticate:
            raise UserError(_('Whatsapp Authentication Failed.'
                              ' Configure Whatsapp Configuration'
                              ' in company setting.'))
        company_id.check_auth()
        venodr_list = []
        msg_data = []
        if self.order_line:
            for line in self.order_line:
                if line.product_id.seller_ids and not line.display_type == 'line_section':
                     if line.product_id.seller_ids[0].name not in venodr_list:
                        venodr_list.append(line.product_id.seller_ids[0].name)

        # print(venodr_list,"vendoor")


        for venodr in venodr_list:
            res = dict(
                (fn, 0.0) for fn in
                ['partner', 'message'])
            order_line = []
            if self.order_line:
                for line in self.order_line:
                    if line.product_id.seller_ids  and not line.display_type == 'line_section':
                        if line.product_id.seller_ids[0].name in venodr:
                            order_line.append(line)
            message = 'hii'
            result_txt = request.env['ir.ui.view'].render_template("odoo_whatsapp_connector.product_data_template", {
                'doc_model': 'sale.order',
                'docs': self,
                'order_line':order_line
            })
            message_txt = ConvertHtmlText.convert_html_to_text(result_txt)
            template_id = self.env['whatsapp.default'].sudo().search([('active', '=', True),('category', '=', 'suplier')], limit=1)
            if template_id:
                message = template_id.default_messege
                if message:
                    message = message.replace("{{name}}", venodr.name)
                    message = message.replace("{{product_details}}", message_txt)
                    message = message.replace("{{number}}", self.name)
            res['partner'] = venodr
            res['message'] = message
            msg_data.append(res)
        print(msg_data,'msg_data')
        thread_start = threading.Thread(
            target=self.send_whatsapp_message_new(msg_data))
        thread_start.start()
        return True
