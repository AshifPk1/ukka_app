# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Loyalty Program',
    'version': '13.0',
    'category': 'Sales',
    'sequence': 6,
    'summary': 'Loyalty Program for Sale ',
    'description': """

This module allows you to define a loyalty program in
the sale, where customers earn loyalty points
and get rewards.

""",
    'depends': ['base','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/settings_view.xml',
        'views/res_partner_view.xml',
        'views/sales_loyalty_views.xml',
        'views/sale_views.xml'

    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
