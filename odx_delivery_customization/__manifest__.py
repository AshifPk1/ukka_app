# -*- coding: utf-8 -*-
#############################################################################
#
#
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Delivery Customization',
    'version': '13.0.1.0.0',
    'category': 'Delivery/Picking Management',
    'summary': "Delivery Details Master Data Creation",
    'description': """

Delivery Details
=======================
Module to manage delivery details,picking details on sale orders and to create the work details of delivery/picking
""",
    'depends': ['base', 'sale', 'sale_stock', 'stock','delivery','website_sale','purchase','account'
                ],
    'data': [
        'security/ir.model.access.csv',
        'security/odx_delivery_customization_security.xml',
        'security/odx_delivery_security_grps.xml',
        'views/res_partner_view.xml',
        'views/delivery_boy_master.xml',
        'views/sale_views.xml',
        'data/account_data.xml',
        'data/ir_sequence_data.xml',
        'views/delivery_picking_views.xml',
        'views/work_details_view.xml',
        'views/settlements_view.xml',
        'views/product_views.xml',
        'views/returned_orders_view.xml',
        'views/account_move_views.xml',
        'views/purchase_views.xml',
        'views/settings_view.xml',
        'views/res_users_view.xml',
        'views/ready_for_pick_up_items_views.xml',
        'views/cart_orders_view.xml',
        'views/product_category_views.xml',
        'views/product_images_view.xml',
        'views/shipping_method_views.xml',
        'views/delivery_slot_time_views.xml',
        'views/banners_view.xml',
        'views/res_users_view.xml',
        'views/res_company_view.xml',
        'views/product_uom_setting_views.xml'

    ],
    'demo': [
    ],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False,
}
