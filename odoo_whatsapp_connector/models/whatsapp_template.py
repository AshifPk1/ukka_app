# -*- coding: utf-8 -*-

import logging
import re
import urllib

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WhatsappDefault(models.Model):
    _name = 'whatsapp.default'
    _description = 'Message default in Whatsapp'

    name = fields.Char(string="Title Template")
    default_messege = fields.Text(string="Message Default")

    category = fields.Selection(
        [('customer', 'Customer'), ('suplier', 'Suplier'), ('delivery_boy', 'Delivery Boy'),
         ('pickup_boy', 'Pickup Boy'),('others','Others'), ('note', 'Thankyou Note')],
        string="Receiver Type")
    active = fields.Boolean('Active')
