# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class MailTemplate(models.Model):
    """Inherit Mail Template."""

    _inherit = 'mail.template'

    is_whatsapp = fields.Boolean(
        string='Is Whatsapp Template',
        default=False
    )

    receiver_type = fields.Selection(
        [('customer', 'Customer'), ('suplier', 'Suplier'), ('delivery_boy', 'Delivery Boy'),
         ('pickup_boy', 'Pickup Boy'),
        ],
        string="Receiver Type")
