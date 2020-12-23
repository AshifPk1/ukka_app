###################################################################################
#
#    Copyright (c) 2017-2019 MuK IT GmbH.
#
#    This file is part of MuK REST API for Odoo 
#    (see https://mukit.at).
#
#    MuK Proprietary License v1.0
#
#    This software and associated files (the "Software") may only be used 
#    (executed, modified, executed after modifications) if you have
#    purchased a valid license from MuK IT GmbH.
#
#    The above permissions are granted for a single database per purchased 
#    license. Furthermore, with a valid license it is permitted to use the
#    software on other databases as long as the usage is limited to a testing
#    or development environment.
#
#    You may develop modules based on the Software or that use the Software
#    as a library (typically by depending on it, importing it and using its
#    resources), but without copying any source code or material from the
#    Software. You may distribute those modules under the license of your
#    choice, provided that this license is compatible with the terms of the 
#    MuK Proprietary License (For example: LGPL, MIT, or proprietary licenses
#    similar to this one).
#
#    It is forbidden to publish, distribute, sublicense, or sell copies of
#    the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###################################################################################

import re
import ast
import json
import urllib
import logging
import random as r
import calendar

from werkzeug import exceptions

from odoo import _, http, release
from odoo.http import request, Response
from odoo.tools import misc, config
from datetime import datetime

from odoo.addons.muk_rest import validators, tools
from odoo.addons.muk_rest.tools.common import parse_value
from odoo.addons.muk_utils.tools.json import ResponseEncoder, RecordEncoder

_logger = logging.getLogger(__name__)
_csrf = config.get('rest_csrf', False)


#
def otpgen():
    otp = ""
    for i in range(4):
        otp += str(r.randint(1, 9))
    return otp


class ModelController(http.Controller):

    # ----------------------------------------------------------
    # Inspection
    # ----------------------------------------------------------

    @http.route([
        '/api/field_names',
        '/api/field_names/<string:model>',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def field_names(self, model, **kw):
        result = request.env[model].fields_get_keys()
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/fields',
        '/api/fields/<string:model>',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def fields(self, model, fields=None, attributes=None, **kw):
        fields = fields and parse_value(fields) or None
        attributes = attributes and parse_value(attributes) or None
        result = request.env[model].fields_get(allfields=fields, attributes=attributes)
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/metadata',
        '/api/metadata/<string:model>',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def metadata(self, model, ids, context=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})
        ids = ids and parse_value(ids) or []
        records = request.env[model].with_context(ctx).browse(ids)
        result = records.get_metadata()
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    # ----------------------------------------------------------
    # Search / Read
    # ----------------------------------------------------------

    @http.route([
        '/api/filter/products',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def search(self, **kw):
        filter_type = kw.get('filter')
        category = kw.get('categ_id')
        companys_id = kw.get('location_id')
        page_number = kw.get('page_number')
        start = end = 0
        if filter_type == '1':

            order = "create_date desc"


        elif filter_type == '2':
            order = "name asc"

        elif filter_type == '3':
            order = "name desc"

        elif filter_type == '4':
            order = "list_price desc"

        elif filter_type == '5':
            order = "list_price asc"

        else:
            order = "id desc"

        if not page_number:
            message = _('Page Number Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if page_number:
            page_number = int(page_number)
            if page_number == 1:
                start = 0
                end = 20
            else:
                start = (page_number - 1) * 20
                end = start + 20
        filter_product = []
        company_id = request.env['res.company'].sudo().browse(int(companys_id))
        products = request.env['product.product'].sudo().search_read(['|', ('company_id', '=', False),
                                                                      ('company_id', '=', company_id.id),
                                                                      ('categ_id.id', '=', category),
                                                                      ('show_in_app', '=', True)],
                                                                     ['id', 'name', 'list_price', 'mrp',
                                                                      'malayalam_name', 'image_256', 'display_uom',
                                                                      'categ_id', 'is_offer', 'uom_id'], order=order)

        if products:

            if len(products) - 1 < start:
                result = {'status': 'Failed', 'message': 'No products in this Page!'}
            else:
                if len(products) < end:
                    filter_product = products[start:len(products)]
                else:
                    filter_product = products[start:end]
                result = {'status': 'Success', 'product_values': filter_product}
        else:
            result = {'status': 'Success', 'message': 'No products under this categroy!',
                      'product_values': filter_product}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    # @http.route([
    #     '/api/filter/products',
    #
    # ], auth="none", type='http', methods=['GET'])
    # @tools.common.parse_exception
    # @tools.common.ensure_database
    # @tools.common.ensure_module()
    # @tools.security.protected()
    # def search(self, context=None, limit=80, offset=0, **kw):
    #     ctx = request.session.context.copy()
    #     ctx.update({'prefetch_fields': False})
    #     ctx.update(context and parse_value(context) or {})
    #
    #     # count = count and misc.str2bool(count) or None
    #     limit = limit and int(limit) or None
    #     offset = offset and int(offset) or None
    #     model = request.env['product.product'].with_context(ctx)
    #
    #     result = {}
    #     order = ""
    #     product_values = []
    #     filter_product=[]
    #     filter_type = kw.get('filter')
    #     category = kw.get('categ_id')
    #     companys_id = kw.get('location_id')
    #     # print(filter_type, "filterrrrr")
    #     # print(category, "cattt")
    #     page_number = kw.get('page_number')
    #     start = 0
    #     end = 0
    #     if page_number:
    #         page_number = int(page_number)
    #         if page_number ==1:
    #             start =0
    #             end = 20
    #         else:
    #             start = (page_number -1) * 20
    #             end = start + 20
    #
    #     domain = [('categ_id.id', '=', category)]
    #     if filter_type == '1':
    #
    #         order = "create_date desc"
    #
    #
    #     elif filter_type == '2':
    #         order = "name asc"
    #
    #     elif filter_type == '3':
    #         order = "name desc"
    #
    #     elif filter_type == '4':
    #         order = "list_price desc"
    #
    #     elif filter_type == '5':
    #         order = "list_price asc"
    #
    #     else:
    #         order = "id desc"
    #     products = model.search(domain, offset=offset, limit=limit, order=order)
    #     company_id = request.env['res.company'].sudo().search([('id', '=', int(companys_id))])
    #
    #     if products:
    #         for product in products:
    #             uom_vals = []
    #             if product.company_id:
    #                 if product.company_id == company_id:
    #                     if product.product_uom_ids:
    #                         for product_uom in product.product_uom_ids:
    #                             uom_vals.append({
    #                                 'uom': product_uom.uom_id.name,
    #                                 'uom_id': product_uom.uom_id.id,
    #                                 'quantity':product_uom.quantity
    #                             })
    #                     product_values.append({
    #                         'product_id': product.id,
    #                         'product': product.name,
    #                         'price': product.lst_price,
    #                         'strike_price': product.mrp,
    #                         'image': product.image_1920,
    #                         'currency': product.currency_id.name,
    #                         'qty_available': product.qty_available,
    #                         'uom_name': uom_vals if product.product_uom_ids else False,
    #                         'malayalam_name': product.malayalam_name,
    #                         'category_id':product.categ_id.id,
    #                         'location':product.company_id.name if product.company_id else False,
    #                         'has_offer': True if product.is_offer else False
    #
    #                     })
    #             else:
    #                 if product.product_uom_ids:
    #                     for product_uom in product.product_uom_ids:
    #                         uom_vals.append({
    #                             'uom': product_uom.uom_id.name,
    #                             'uom_id': product_uom.uom_id.id,
    #                             'quantity': product_uom.quantity
    #                         })
    #                 product_values.append({
    #                     'product_id': product.id,
    #                     'product': product.name,
    #                     'price': product.lst_price,
    #                     'strike_price': product.mrp,
    #                     'image': product.image_1920,
    #                     'currency': product.currency_id.name,
    #                     'qty_available': product.qty_available,
    #                     'uom_name': uom_vals if product.product_uom_ids else False,
    #                     'malayalam_name': product.malayalam_name,
    #                     'category_id': product.categ_id.id,
    #                     'location': product.company_id.name if product.company_id else False,
    #                     'has_offer': True if product.is_offer else False
    #
    #                 })
    #
    #         if len(product_values) - 1 < start:
    #             result = {'status': 'Failed', 'message': 'No products in this Page!'}
    #         else:
    #             if len(product_values) < end:
    #                 for i in range(start, len(product_values)):
    #                     filter_product.append(product_values[i])
    #             else:
    #                 for i in range(start, end):
    #                     filter_product.append(product_values[i])
    #
    #             result = {
    #                 'status': 'Success',
    #                 'products': filter_product
    #             }
    #     else:
    #         result = {
    #             'status': 'Failed',
    #             'message': 'No products under this category!',
    #             'products': product_values
    #         }
    #     content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
    #     return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/name',
        '/api/name/<string:model>',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def name(self, model, ids, context=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})
        ids = ids and parse_value(ids) or []
        records = request.env[model].with_context(ctx).browse(ids)
        result = records.name_get()
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/read/product',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def read_product(self, id, **kw):
        id = id and parse_value(id) or []
        product = request.env['product.product'].sudo().browse(id)
        product_list = []

        if product:
            images = []
            uom_vals = []
            if product.product_images_ids:
                for product_image in product.product_images_ids:
                    images.append(product_image.image_000)
            if product.product_uom_ids:
                for product_uom in product.product_uom_ids:
                    uom_vals.append({
                        'uom': product_uom.uom_id.name,
                        'uom_id': product_uom.uom_id.id,
                        'quantity': product_uom.quantity,
                        'id': product_uom.id,
                        'price': product_uom.price,
                        'strike_price': product_uom.strike_price
                    })

            product_list.append({
                'product_id': product.id,
                'product': product.name,
                'price': product.lst_price,
                'strike_price': product.mrp,
                'image': product.image_1920,
                'currency': product.currency_id.name,
                'qty_available': product.qty_available,
                'uom_name': uom_vals if product.product_uom_ids else False,
                'category_id': product.categ_id.id if product.categ_id else False,
                'image_list': images if product.product_images_ids else False,
                'malayalam_name': product.malayalam_name,
                'description': product.description_sale,
                'location': product.company_id.name if product.company_id else False,
                'has_offer': True if product.is_offer else False

            })
            result = {'status': 'Success', 'message': 'Products under this categroy!',
                      'product_values': product_list}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/read',
        '/api/read/<string:model>',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def read(self, model, ids, fields=None, context=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})
        ids = ids and parse_value(ids) or []
        fields = fields and parse_value(fields) or None
        records = request.env[model].with_context(ctx).browse(ids)
        result = records.read(fields=fields)
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/search_read/products',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def search_read_products(self, fields=None, **kw):
        fields = fields and parse_value(fields) or None
        category_id = kw.get('categ_id')
        page_number = kw.get('page_number')
        companys_id = kw.get('location_id')
        domain = [('categ_id.id', '=', category_id)]
        result = request.env['product.product'].search_read(domain, fields=fields, order='id desc')
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route(['/api/featured/products', ], auth="none", type='http', methods=['GET'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def featured_products(self, **kw):

        companys_id = kw.get('location_id')
        page_number = kw.get('page_number')
        # domain = [('is_offer', '=', True)]
        start = end = 0

        if not page_number:
            message = _('Page Number Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if page_number:
            page_number = int(page_number)
            if page_number == 1:
                start = 0
                end = 20
            else:
                start = (page_number - 1) * 20
                end = start + 20
        filter_product = []
        company_id = request.env['res.company'].sudo().browse(int(companys_id))
        products = request.env['product.product'].sudo().search_read(['|', ('company_id', '=', False),
                                                                      ('company_id', '=', company_id.id),
                                                                      ('is_featured', '=', True),
                                                                      ('show_in_app', '=', True)],
                                                                     ['id', 'name', 'list_price', 'mrp',
                                                                      'malayalam_name', 'image_256', 'display_uom',
                                                                      'categ_id', 'is_offer', 'uom_id', 'is_featured'],
                                                                     order='sequence')

        if products:

            if len(products) - 1 < start:
                result = {'status': 'Failed', 'message': 'No products in this Page!'}
            else:
                if len(products) < end:
                    filter_product = products[start:len(products)]
                else:
                    filter_product = products[start:end]
                result = {'status': 'Success', 'product_values': filter_product}
        else:
            result = {'status': 'Success', 'message': 'No products under this categroy!',
                      'product_values': filter_product}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route(['/api/offer/products', ], auth="none", type='http', methods=['GET'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def search_products(self, **kw):

        companys_id = kw.get('location_id')
        page_number = kw.get('page_number')
        # domain = [('is_offer', '=', True)/products]
        start = end = 0

        if not page_number:
            message = _('Page Number Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if page_number:
            page_number = int(page_number)
            if page_number == 1:
                start = 0
                end = 20
            else:
                start = (page_number - 1) * 20
                end = start + 20
        filter_product = []
        company_id = request.env['res.company'].sudo().browse(int(companys_id))
        products = request.env['product.product'].sudo().search_read(['|', ('company_id', '=', False),
                                                                      ('company_id', '=', company_id.id),
                                                                      ('is_offer', '=', True),
                                                                      ('show_in_app', '=', True)],
                                                                     ['id', 'name', 'list_price', 'mrp',
                                                                      'malayalam_name', 'image_256', 'display_uom',
                                                                      'categ_id', 'is_offer', 'uom_id'],
                                                                     order='sequence')

        if products:

            if len(products) - 1 < start:
                result = {'status': 'Failed', 'message': 'No products in this Page!'}
            else:
                if len(products) < end:
                    filter_product = products[start:len(products)]
                else:
                    filter_product = products[start:end]
                result = {'status': 'Success', 'product_values': filter_product}
        else:
            result = {'status': 'Success', 'message': 'No products under this categroy!',
                      'product_values': filter_product}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/search_read',
        '/api/search_read/<string:model>',
        '/api/search_read/<string:model>/<string:order>',
        '/api/search_read/<string:model>/<int:limit>/<string:order>',
        '/api/search_read/<string:model>/<int:limit>/<int:offset>/<string:order>'
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def search_read(self, model, domain=None, fields=None, context=None, limit=80, offset=0, order=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})
        domain = domain and parse_value(domain) or []
        fields = fields and parse_value(fields) or None
        limit = limit and int(limit) or None
        offset = offset and int(offset) or None
        model = request.env[model].with_context(ctx)
        result = model.search_read(domain, fields=fields, offset=offset, limit=limit, order=order)
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/read_group',
        '/api/read_group/<string:model>',
        '/api/read_group/<string:model>/<string:orderby>',
        '/api/read_group/<string:model>/<int:limit>/<string:orderby>',
        '/api/read_group/<string:model>/<int:limit>/<int:offset>/<string:orderby>'
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def read_group(self, model, domain, fields, groupby, context=None, offset=0, limit=None, orderby=False, lazy=True,
                   **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})
        domain = domain and parse_value(domain) or []
        fields = fields and parse_value(fields) or []
        groupby = groupby and parse_value(groupby) or []
        limit = limit and int(limit) or None
        offset = offset and int(offset) or None
        lazy = misc.str2bool(lazy)
        model = request.env[model].with_context(ctx)
        result = model.read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/categories',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def categories(self, **kw):

        result = {}
        categories_list = []
        categories = request.env['product.category'].search_read([('is_delivery', '=', False)],
                                                                 ['id', 'name', 'parent_id', 'image_256',
                                                                  'is_restuarant_category', 'company_id',
                                                                  'is_miscellaneous_category'],
                                                                 order='sequence')

        if categories:

            result = {'status': 'Success', 'category_values': categories}
        else:
            result = {'status': 'Failed', 'message': 'No categories found!', 'category_values': categories_list}

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/sub_categories',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def sub_categories(self, **kw):

        result = {}
        sub_categories = []
        categ_id = kw.get('categ_id')

        categories = request.env['product.category'].search([('parent_id.id', '=', categ_id)])
        if categories:
            for category in categories:
                sub_categories.append({
                    'sub_category_id': category.id,
                    'sub_category_name': category.name,

                })

            result = {'status': 'Success', 'sub_category_values': sub_categories}
        else:
            result = {'status': 'Failed', 'message': 'No subcategories'}

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    # ----------------------------------------------------------
    # Create / Update / Delete
    # ----------------------------------------------------------

    @http.route([
        '/api/create',
        '/api/create/<string:model>',
    ], auth="none", type='http', methods=['POST'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['create'])
    def create(self, model, values=None, context=None, **kw):
        ctx = request.session.context.copy()
        # print(ctx)
        ctx.update(context and parse_value(context) or {})

        values = values and parse_value(values) or {}
        # print(values)
        model = request.env[model].with_context(ctx)
        result = model.create(values).ids
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/sign_up'
    ], auth="none", type='http', methods=['POST'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['create'])
    def register_user(self, values=None, context=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})
        partner_values = {}
        result = {}
        user_group_portal = request.env.ref('base.group_portal')
        groups = {
            'groups_id': [(6, 0, [user_group_portal.id])]
        }

        values = values and parse_value(values) or {}
        values.update(groups)
        model = request.env['res.users'].with_context(ctx)
        # print(values,"vals")
        user = request.env['res.users'].sudo().search([('login', '=', values.get('login'))])
        message = ''
        status = ''
        otp_values = {}
        if not user:
            if not values.get('login'):
                message = _('Please provide mobile number!')
                status = _('Failed')
            elif not values.get('password'):
                message = _('Please set a password!')
                status = _('Failed')
            elif not values.get('name'):
                message = _('Please provide your name!')
                status = _('Failed')
            elif not values.get('city'):
                message = _('Please provide location!')
                status = _('Failed')
            else:
                message = _('Successful! Provide OTP to continue!')
                status = _('Success')
                otp = ""
                for i in range(4):
                    otp += str(r.randint(1, 9))
                otp_values = {
                    'msg': 'Your OTP is',
                    'OTP': otp
                }
                result.update(otp_values)
                record = request.env['gateway_setup'].sudo().search([], limit=1)
                mobile = '+' + values.get('mobile')
                record.update({
                    'mobile': mobile,
                    'message': otp,
                })

                try:
                    record.sms_test_action()
                except:
                    pass

            result = {'status': status, 'message': message, 'OTP_details': otp_values}

            # print(result,"usercerar")


        else:
            result = {'status': 'Failed', 'message': _('Already existing customer!'),
                      }

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/user/create'
    ], auth="none", type='http', methods=['POST'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['create'])
    def portaluser(self, values=None, context=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})
        partner_values = {}
        result = {}
        user_group_portal = request.env.ref('base.group_portal')
        phone_code = kw.get('phone_code')
        countrys_id = request.env['res.country'].search([('phone_code', '=', phone_code)], limit=1)
        # print(countrys_id.name)

        companies = request.env['res.company'].search([])
        company_list = []
        for company in companies:
            company_list.append(company)
        groups = {
            'groups_id': [(6, 0, [user_group_portal.id])],
            'company_ids': [(6, 0, [company.id for company in company_list])],
            'country_id': countrys_id.id
        }

        values = values and parse_value(values) or {}
        values.update(groups)

        model = request.env['res.users'].with_context(ctx)
        # print(values,"vals")
        user = request.env['res.users'].search([('login', '=', values.get('login'))])
        # print(user.name,"username")
        message = ''
        status = ''

        if not user:
            if not values.get('login'):
                message = _('Please provide mobile number!')
                status = _('Failed')
            elif not values.get('password'):
                message = _('Please set a password!')
                status = _('Failed')
            elif not values.get('name'):
                message = _('Please provide your name!')
                status = _('Failed')
            elif not values.get('company_id'):
                message = _('Please provide location!')
                status = _('Failed')
            else:

                message = _('Successful! Enjoy Shopping!!')
                status = _('Success')

                user_id = model.sudo().create(values)
                # if user_id:
                #     vals = {
                #         'name':'client api',
                #         'state': 'client_credentials',
                #         'security': 'basic',
                #         'user':user_id.id
                #
                #     }
                #     token_id = request.env['muk_rest.oauth2'].create(vals)

                partner = request.env['res.partner'].search([('id', '=', user_id.partner_id.id)])
                if partner:
                    partner.company_id = user_id.company_id.id
                partner_values = {'id': partner.id, 'name': partner.name, 'mobile': partner.mobile,
                                  'location': partner.city, 'selected_location': partner.company_id.name
                                  }
                result.update(partner_values)

            result = {'status': status, 'message': message, 'partner_details': partner_values}

            # print(result, "usercerar")


        else:
            result = {'status': 'Failed', 'message': _('Already existing customer!'),
                      }

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/redeem/coins'
    ], auth="none", type='http', methods=['POST'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['create'])
    def redeem_points(self, **kw):
        partner = kw.get('partner_id')
        company_id = kw.get('location_id')
        if not partner:
            message = _('Customer Id Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])
        if not partner_id:
            message = _('Customer Not Found!')
            status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        sale_order = request.env['sale.order'].sudo().search(
            [('partner_id', '=', int(partner)), ('state', '=', 'draft'),
             ('order_placed', '=', False), ('delivery_picking_id', '=', False), ('company_id', '=', int(company_id))],
            limit=1)
        if sale_order:
            delivery_charge = ''
            rate = {}
            if sale_order.carrier_id.delivery_type in ('fixed', 'base_on_rule'):
                rate = sale_order.carrier_id.rate_shipment(sale_order)
            if rate:
                delivery_charge = rate.get('price')
            redeem_values = sale_order.redeem_loyalty_points()
            if not redeem_values:
                result = {
                    'status': 'Success',
                    'message': 'No options available to redeem!',
                    'order_value': sale_order.amount_total - delivery_charge,
                    'order_id': sale_order.id,
                    'grand_total': sale_order.amount_total,
                    'delivery_charge': delivery_charge,
                    'balance_ukka_coins': sale_order.partner_id.loyalty_points

                }
                content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                return Response(content, content_type='application/json;charset=utf-8', status=200)

            else:
                content = json.dumps(redeem_values, sort_keys=True, indent=4, cls=ResponseEncoder)
                return Response(content, content_type='application/json;charset=utf-8', status=200)

        else:
            result = {
                'status': 'Failed',
                'message': 'This order is not found!'
            }
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/order/place'
    ], auth="none", type='http', methods=['POST'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['create'])
    def order_place(self, product_ids=None, values=None, **kw):

        partner = kw.get('partner_id')
        company_id = kw.get('location_id')
        delivery_method = kw.get('delivery_method')
        transaction_id = kw.get('transaction_id')
        payment_methods = kw.get('payment_methods')
        payment_amount = kw.get('payment_amount')

        if not partner:
            message = _('Customer Id Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])
        if not partner_id:
            message = _('Customer Not Found!')
            status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

        sale_order = request.env['sale.order'].sudo().search(
            [('partner_id', '=', int(partner)), ('state', '=', 'draft'), ('order_placed', '=', False),
             ('company_id', '=', int(company_id))], limit=1)
        delivery_methods = request.env['delivery.carrier'].search([('id', '=', int(delivery_method))])
        if not delivery_method:
            result = {
                'status': 'Failed',
                'message': 'No such delivery methods!'
            }

            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

        if sale_order:
            sale_order.write({
                'order_placed': True,
                'order_method': 'app',
                'carrier_id': delivery_methods.id,
                'transaction_id': transaction_id,
                'payment_methods': payment_methods,
                'payment_amount': payment_amount,
                'order_placed_date': datetime.now()

            })
            # sale_order._onchange_order_place()
            sale_order.check_loyalty_program()
            sale_order.add_redeem_line()
            # sale_order.show_notification()
            existing_sale_order_line = request.env['sale.order.line'].sudo().search(
                [('order_id', '=', sale_order.id), ('is_delivery', '=', True)], limit=1)
            if existing_sale_order_line:
                delivery_charge = ''
                rate = {}
                if delivery_methods.delivery_type in ('fixed', 'base_on_rule'):
                    rate = delivery_methods.rate_shipment(sale_order)
                if rate:
                    delivery_charge = rate.get('price')
                # adding delivery_method as a product in order place
                existing_sale_order_line.write({
                    'product_id': delivery_methods.product_id.id,
                    'name': delivery_methods.name,
                    'product_uom_qty': 1,
                    'price_unit': delivery_charge,
                    'tax_id': False,
                    'is_delivery': True
                })
                # print(existing_sale_order_line,"exist")

            # carrier = delivery_methods.id,
            # amount = delivery_methods.fixed_price
            # sale_order.action_open_delivery_wizard()
            else:
                delivery_charge = ''
                rate = {}
                if delivery_methods.delivery_type in ('fixed', 'base_on_rule'):
                    rate = delivery_methods.rate_shipment(sale_order)
                if rate:
                    delivery_charge = rate.get('price')
                # print("hiii")
                sale_order.order_line.create({
                    'order_id': sale_order.id,
                    'name': delivery_methods.name,
                    'product_uom_qty': 1,
                    'product_uom': delivery_methods.product_id.uom_id.id if delivery_methods.product_id.uom_id else False,
                    'product_id': delivery_methods.product_id.id if delivery_methods.product_id else False,
                    'price_unit': delivery_charge,
                    'tax_id': False,
                    'is_delivery': True,

                })
            sale_order.new_orders_notify()

            result = {
                'status': 'Success',
                'message': 'Your Order has been placed!',
                'order_num': sale_order.name,
                'order_id': sale_order.id,
                'coins': sale_order.earned_points
            }
        else:
            result = {
                'status': 'Failed',
                'message': 'Please Add Some Item To Your Cart in this Location!'
            }

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/write',
        '/api/write/<string:model>',
    ], auth="none", type='http', methods=['PUT'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['write'])
    def write(self, model, ids=None, values=None, context=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})
        ids = ids and parse_value(ids) or []
        values = values and parse_value(values) or {}
        records = request.env[model].with_context(ctx).browse(ids)
        result = records.write(values)
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/delivery_address',

    ], auth="none", type='http', methods=['PUT', 'GET'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['write'])
    def write(self, ids=None, values=None, **kw):

        if request.httprequest.method.upper() == 'PUT':
            ctx = request.session.context.copy()
            # ctx.update(context and parse_value(context) or {})
            ids = ids and parse_value(ids) or []
            values = values and parse_value(values) or {}

            if not values.get('street'):
                message = _('Please give your address!')
                status = _('Failed')
            elif not values.get('city'):
                message = _('Please give your place!')
                status = _('Failed')

            elif not values.get('location_link'):
                message = _('Please provide location link!')
                status = _('Failed')
            elif not values.get('ref'):
                message = _('Please select location on maps to update pin location!')
                status = _('Failed')

            else:
                records = request.env['res.partner'].browse(ids)

                records.write({

                    'child_ids': [(0, 0, {
                        'type': 'delivery',
                        'name': records.name,
                        'street': values.get('street'),
                        'location_link': values.get('location_link'),
                        'selected_address': True,
                        'city': values.get('city'),

                        'street2': values.get('street2'),
                        'zip': values.get('zip') if values.get('zip') else ' ',
                        'phone': values.get('phone'),
                        'ref': values.get('ref')

                    })]
                })

                message = _('Successfully added your Delivery Address!')
                status = _('Success')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if request.httprequest.method.upper() == 'GET':

            records = request.env['res.partner'].sudo().search([('id', '=', ids)])
            delivery_addresses = []
            if records.child_ids:
                for address_id in records.child_ids:
                    delivery_addresses.append({
                        'id': address_id.id,
                        'name': address_id.name,
                        'place': address_id.city,
                        'address': address_id.street,
                        'zip': address_id.zip or '',
                        'landmark': address_id.street2 or '',
                        'alternate_phone': address_id.phone or '',
                        'mobile': records.mobile,
                        'location_link': address_id.location_link or '',
                        'ref': address_id.ref
                    }

                    )

                result = {'status': 'Success', 'delivery_addresses': delivery_addresses}
            else:
                result = {'status': 'Failed', 'message': 'No other addresses!!'}
            # print(result,"ress")
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/edit/delivery_address',

    ], auth="none", type='http', methods=['PUT'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['write'])
    def edit_address(self, ids=None, values=None, **kw):

        ids = ids and parse_value(ids) or []
        values = values and parse_value(values) or {}
        try:

            records = request.env['res.partner'].browse(ids)
            records.write(values)
            message = _('Successfully edited your Delivery Address!')
            status = _('Success')
        except Exception:
            message = _('Opz!Something went wrong!!')
            status = _('Failed')
        result = {'status': status, 'message': message}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/set/delivery_address',

    ], auth="none", type='http', methods=['PUT'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['write'])
    def create(self, **kw):
        id = kw.get('id')
        message = ''
        status = ''
        if id:
            try:
                delivery_adress_id = request.env['res.partner'].search([('id', '=', int(id))])
                if delivery_adress_id:
                    partner = delivery_adress_id.parent_id
                    address_list = []
                    for child_id in partner.child_ids:
                        address_list.append(child_id)
                    for item in address_list:
                        item.selected_address = False
                        if item.id == delivery_adress_id.id:
                            item.write({
                                'selected_address': True
                            })
                    message = _('Successfully set the delivery address!')
                    status = _('Success')
                else:
                    message = _('No such address!')
                    status = _('Failed')
            except Exception:
                message = _('Something went wrong!')
                status = _('Failed')
        else:
            message = _('Please specify id')
            status = _('Failed')

        result = {'status': status, 'message': message}

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/get/terms_and_conditions',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def get_terms(self, **kw):
        companys_id = kw.get('location_id')
        if not companys_id:
            message = _('Location id  is not given')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        company_id = request.env['res.company'].sudo().search([('id', '=', int(companys_id))])
        if not company_id:
            message = _('No such location found')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if company_id.terms_and_conditions:
            message = _('Terms and Conditions')
            status = _('Success')
            result = {'status': status, 'message': message, 'terms_conditions': company_id.terms_and_conditions}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/top/selling_products',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def top_selling_products(self, **kw):
        if kw.get('company'):
            company = int(kw['company'])

            date = datetime.today()
            start_date = datetime(date.year, date.month, 1)
            end_date = datetime(date.year, date.month, calendar.mdays[date.month])

            query_picking = """select pp.malayalam_name as malayalam_name,pt.list_price as list_price,pp.mrp as mrp,pp.is_offer 
                               as is_offer,pt.name as product_name,pt.categ_id as categ_id,pp.id as product_id, sum(sl.product_uom_qty) as sale_qty 
                                                 from sale_order_line sl
                                                        inner join product_product pp on pp.id = sl.product_id
                                                        inner join product_template pt on pt.id = pp.product_tmpl_id
                                                        inner join sale_order so on so.id = sl.order_id
                                                        left join res_company c ON (pt.company_id is null or pt.company_id = c.id)
                                                 where  pp.show_in_app = True and
                                                        pt.type != 'service' and
                                                        pt.company_id = '""" + str(company) + """' and
                                                        so.state = 'sale' and
                                                        so.date_order::date between '""" + str(
                start_date) + """' and '""" + str(end_date) + """'
                                                 group by pt.name, pp.id,pt.list_price,pt.categ_id
                                                 order by sale_qty desc limit 20"""

            request.cr.execute(query_picking)
            results = request.cr.dictfetchall()
            if results:
                for item in results:
                    id = item.get('product_id')
                    product = request.env['product.product'].sudo().browse(id)
                    item['image'] = product.image_128
                    item['display_uom'] = product.display_uom.name
                    item['uom_id'] = product.uom_id.id
                products = {
                    'status': 'Success',
                    'message': 'Top Selling Products',
                    'product_values': results
                }
            else:
                products = {
                    'status': 'Failed',
                    'message': 'No Items to display',

                }

            content = json.dumps(products, sort_keys=True, indent=4, cls=ResponseEncoder)

            return Response(content, content_type='application/json;charset=utf-8', status=200)
        else:
            products = {
                'status': 'Failed',
                'message': 'Please select a location',

            }
            content = json.dumps(products, sort_keys=True, indent=4, cls=ResponseEncoder)

            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/get/ukka_coins',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def get_user_ukka_coins(self, **kw):
        partner = kw.get('partner_id')
        if not partner:
            message = _('Customer Id Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])
        if not partner_id:
            message = _('Customer Not Found!')
            status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        else:
            message = _('Congrats Your Total Coins!')
            status = _('Success')

            result = {
                'status': status,
                'message': message,
                'coins': partner_id.loyalty_points
            }
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/get_selected_address',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def get_selected_address(self, **kw):
        partner = kw.get('partner_id')
        selected_address = {}
        result = {}
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])
        if partner_id.child_ids:
            for child_id in partner_id.child_ids:
                if child_id.selected_address:
                    selected_address = {
                        'address_id': child_id.id,
                        'name': child_id.name,
                        'place': child_id.city,
                        'address': child_id.street,
                        'zip': child_id.zip or '',
                        'landmark': child_id.street2 or '',
                        'alternate_phone': child_id.phone or '',
                        'mobile': partner_id.mobile
                    }
            result = {'status': 'Success', 'address': selected_address}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        else:
            result = {'status': 'Failed', 'message': 'No address selected for this partner',
                      'address': selected_address}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/unlink',
        '/api/unlink/<string:model>',
    ], auth="none", type='http', methods=['DELETE'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['unlink'])
    def unlink(self, model, ids=None, context=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})
        ids = ids and parse_value(ids) or []
        records = request.env[model].with_context(ctx).browse(ids)
        result = records.unlink()
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/cancel/order'
    ], auth="none", type='http', methods=['PUT'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['write'])
    def order_cancel(self, product_ids=None, values=None, **kw):
        partner = kw.get('partner_id')

        order_id = kw.get('order_id')

        if not partner:
            message = _('Customer Id Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])

        if not partner_id:
            message = _('Customer Not Found!')
            status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

        sale_order = request.env['sale.order'].sudo().search(
            [('id', '=', int(order_id)), ('partner_id', '=', int(partner)), ('state', '=', 'draft'),
             ('order_placed', '=', True), ('delivery_picking_id', '=', False)], limit=1)

        if sale_order:
            sale_order.write({
                'cancelled_order': True,
                'order_method': 'app'
            })
            sale_order.points_in_canceled_order()
            result = {
                'status': 'Success',
                'message': 'Your Order has been canceled.Please check order history to know your cancelled items'

            }
        else:
            result = {
                'status': 'Failed',
                'message': 'No orders to cancel!'
            }

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/add_cart',
    ], auth="none", type='http', methods=['PUT'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['create'])
    def add_to_cart(self, values=None, context=None, **kw):
        partner = kw.get('partner_id')
        product = kw.get('product_id')
        companys_id = kw.get('location_id')
        qty = kw.get('qty')
        ordered_qty = kw.get('ordered_qty')
        uom_id = kw.get('uom_id')
        product_uom_set = kw.get('product_uom_id')
        price = kw.get('price')
        if not partner or not product:
            if not partner:
                message = _('Customer Id Not Given!')
                status = _('Failed')
            if not product:
                message = _('Product Id Not Given!')
                status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])
        product_id = request.env['product.product'].sudo().search([('id', '=', int(product))])
        company_id = request.env['res.company'].sudo().search([('id', '=', int(companys_id))])
        # if product_uom_id:
        #    product_uom_ids = request.env['product.uom.setting'].sudo().search([('id','=',int(product_uom_id))])
        if product_id.company_id:
            if product_id.company_id != company_id:
                message = _('Please select the products from the selected location')
                status = _('Failed')
                result = {'status': status, 'message': message}
                content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                return Response(content, content_type='application/json;charset=utf-8', status=200)

        if not partner_id or not product_id:
            if not partner_id:
                message = _('Customer Not Found!')
                status = _('Failed')
            if not product_id:
                message = _('Product Not Found!')
                status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

        existing_sale_order_line = ''
        sale_order = request.env['sale.order'].sudo().search(
            [('partner_id', '=', int(partner)), ('state', '=', 'draft'), ('order_placed', '=', False),
             ('company_id', '=', company_id.id)], limit=1)
        if sale_order:
            existing_sale_order_line = request.env['sale.order.line'].sudo().search(
                [('order_id', '=', sale_order.id), ('product_id', '=', product_id.id),
                 ('product_uom', '=', int(uom_id)), ('product_set_uom', '=', product_uom_set)], limit=1)
        if not sale_order:
            sale_order = request.env['sale.order'].sudo().create({
                'partner_id': int(partner),
                'partner_shipping_id': partner_id.id,
                'partner_invoice_id': partner_id.id,
                'order_method': 'app',
                'state': 'draft',
                'company_id': company_id.id
            })
        if existing_sale_order_line:
            actual_qty = 1
            if product_uom_set:
                display_qty = product_uom_set.split(',')
                if display_qty:
                    actual_qty_lst = display_qty[0].split(' ')
                    if actual_qty_lst:
                        actual_qty = float(actual_qty_lst[0])
            total_orderd_qty = float(qty) * actual_qty
            existing_sale_order_line.write({
                'product_uom_qty': total_orderd_qty,
                'ordered_qty': ordered_qty,
            })

            message = _('Successfully Update The Quantity!')
            status = _('Success')
            line_id = existing_sale_order_line.id,
            line_price_subtotal = existing_sale_order_line.price_subtotal,
            line_unit_price = existing_sale_order_line.price_unit
        else:
            # so quantity is derived from product_uom_set and multiplied and pased with ordered qty
            actual_qty = 1
            if product_uom_set:
                display_qty = product_uom_set.split(',')
                if display_qty:
                    actual_qty_lst = display_qty[0].split(' ')
                    if actual_qty_lst:
                        actual_qty = float(actual_qty_lst[0])
            total_orderd_qty = float(qty) * actual_qty

            sale_order_line = request.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'product_id': product_id.id,
                'product_uom_qty': total_orderd_qty,
                'product_uom': int(uom_id),
                'ordered_qty': ordered_qty,
                'product_set_uom': product_uom_set,
                # 'price_unit': float(price)
            })
            message = _('Item Successfully Added To Your Cart!')
            status = _('Success')
            line_id = sale_order_line.id,
            line_price_subtotal = sale_order_line.price_subtotal,
            line_unit_price = sale_order_line.price_unit

        result = {'status': status, 'message': message, 'line_id': line_id, 'line_price_subtotal': line_price_subtotal,
                  'line_unit_price': line_unit_price}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/item/removal',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def item_clear(self, **kw):
        line_id = kw.get('line_id')
        sale_order_line = request.env['sale.order.line'].sudo().browse(int(line_id))
        # print(sale_order_line,"lineeeeeeeee")

        if sale_order_line:
            sale_order_line.unlink()
            message = _('Item successfully removed from your cart!')
            status = _('Success')
            line_id = False,
            line_price_subtotal = False,
            line_unit_price = False
            result = {'status': status, 'message': message, 'line_id': line_id,
                      'line_price_subtotal': line_price_subtotal,
                      'line_unit_price': line_unit_price}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/clear/cart',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def clear_cart(self, **kw):
        partner = kw.get('partner_id')
        companys_id = kw.get('location_id')

        if not partner:
            message = _('Customer Id Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])

        if not partner_id:
            message = _('Customer Not Found!')
            status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        company_id = request.env['res.company'].sudo().search([('id', '=', int(companys_id))])

        sale_order = request.env['sale.order'].sudo().search(
            [('partner_id', '=', int(partner)), ('state', '=', 'draft'), ('order_placed', '=', False),
             ('company_id', '=', company_id.id)], limit=1)

        if sale_order:
            for line in sale_order.order_line:
                line.unlink()
            status = 'Success',
            message = 'Cart is cleared'
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/my_cart',

    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def get_my_cart(self, **kw):
        partner = kw.get('partner_id')
        companys_id = kw.get('location_id')
        # print(companys_id,"params")
        product_list = []
        if not partner:
            message = _('Customer Id Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])

        if not partner_id:
            message = _('Customer Not Found!')
            status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        company_id = request.env['res.company'].sudo().search([('id', '=', int(companys_id))])
        # print(company_id, "company")
        sale_order = request.env['sale.order'].sudo().search(
            [('partner_id', '=', int(partner)), ('state', '=', 'draft'), ('order_placed', '=', False),
             ('company_id', '=', company_id.id)], limit=1)
        # print(sale_order)
        # print(sale_order.company_id,"companyyy in sale order")
        result = {}
        if sale_order:

            # print("hello")

            for line in sale_order.order_line:
                images = []
                uom_vals = []
                if line.product_id.product_images_ids:
                    for product_image in line.product_id.product_images_ids:
                        images.append(product_image.image_000)
                if line.product_id.product_uom_ids:
                    for product_uom in line.product_id.product_uom_ids:
                        uom_vals.append({

                            'uom': product_uom.uom_id.name,
                            'uom_id': product_uom.uom_id.id,
                            'quantity': product_uom.quantity,
                            'id': product_uom.id,
                            'price': product_uom.price,
                            'strike_price': product_uom.strike_price

                        })

                if not line.product_uom_qty == 0 or line.product_id.type == 'service':
                    product_list.append({
                        'line_id': line.id,
                        'product_id': line.product_id.id,
                        'product_type': line.product_id.type,
                        'product': line.product_id.name if line.product_id else False,
                        'image': line.product_id.image_128 if line.product_id.image_128 else False,
                        'is_delivery': True if line.is_delivery else False,
                        'qty': line.product_uom_qty,
                        'price': line.price_unit,
                        'strike_price': line.product_id.mrp,
                        'price_subtotal': line.price_subtotal,
                        'uom_name': uom_vals if line.product_id.product_uom_ids else False,
                        'qty_available': line.product_id.qty_available,
                        'currency': line.product_id.currency_id.name,
                        'category_id': line.product_id.categ_id.id if line.product_id.categ_id else False,
                        'image_list': images if line.product_id.product_images_ids else False,
                        'malayalam_name': line.product_id.malayalam_name,
                        'description': line.product_id.description_sale,
                        'has_offer': True if line.product_id.is_offer else False,
                        'ordered_qty': line.ordered_qty,
                        'display_uom': line.product_id.display_uom.name,
                        'product_set_uom': line.product_set_uom
                    })

            result = {'status': 'Success', 'Products': product_list}
        else:
            result = {'status': 'Success', 'message': 'Your Cart Is Empty!'}

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/my_orders',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def my_orders(self, fields=None, context=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})

        partner = kw.get('partner_id')

        # delivery_state = {
        #     'pending': 'Picking',
        #     'ready': 'Delivering',
        #     'confirmed': 'Delivered'
        # }
        if not partner:
            message = _('Customer Id Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])
        if not partner_id:
            message = _('Customer Not Found!')
            status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

        sale_order = request.env['sale.order'].sudo().search(
            ['|', ('delivery_picking_id', '=', False), ('delivery_picking_id.state', '!=', 'confirmed'),
             ('partner_id', '=', int(partner)), ('order_placed', '=', True), ('state', '=', 'draft'),
             ('cancelled_order', '=', False)], order='create_date desc')
        ids = ''
        if sale_order:
            order_list = []
            delivery_amount = ''
            for order in sale_order:
                product_list = []
                estimated_time = ''
                delivry_amount = ''
                if order.carrier_id:

                    if not order.carrier_id.scheduled_delivery:
                        estimated_time = order.carrier_id.delivery_time

                    else:
                        estimated_time = False

                for line in order.order_line:
                    uom_vals = []
                    if line.is_delivery:
                        delivry_amount = line.price_unit

                    if line.product_id.product_uom_ids:
                        for product_uom in line.product_id.product_uom_ids:
                            uom_vals.append({
                                'uom': product_uom.uom_id.name,
                                'uom_id': product_uom.uom_id.id,
                                'quantity': product_uom.quantity,
                                'id': product_uom.id
                            })

                    product_list.append({
                        'line_id': line.id,
                        'product_id': line.product_id.id,
                        'is_delivery': True if line.is_delivery else False,
                        'product': line.product_id.name if line.product_id else False,
                        # 'image': line.product_id.image_1920 if line.product_id else False,
                        'ordered_qty': line.ordered_qty,
                        'qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'price_subtotal': line.price_subtotal,
                        'uom_name': uom_vals if line.product_id.product_uom_ids else False,
                        'product_set_uom': line.product_set_uom,
                        'malayalam_name': line.product_id.malayalam_name,
                        'description': line.product_id.description_sale,
                        'category_id': line.product_id.categ_id.id if line.product_id.categ_id else False,

                    })

                # print(order.delivery_picking_id.state,'statete')
                # print(order.name,'order')

                order_list.append({
                    'order_id': order.id,
                    'order_no': order.name,
                    'date': order.create_date,
                    'partner': order.partner_id.name if order.partner_id else False,
                    'products': product_list,
                    'delivery_charge': delivry_amount,
                    'amount_total': order.amount_total,
                    'delivery_method': order.carrier_id.id if order.carrier_id else False,
                    'delivery_method_name': order.carrier_id.name if order.carrier_id else False,
                    'estimated_time': estimated_time,
                    'location': order.company_id.id if order.company_id else False,
                    # 'order_status': delivery_state[order.delivery_picking_id.state]
                })

            result = {'status': 'Success', 'message': 'Your Orders!', 'order_values': order_list}
        else:
            result = {'status': 'Failed', 'message': 'You have not placed any orders!'}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/order/status',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def my_order_status(self, **kw):
        order_id = kw.get('order_id')
        delivery_state = {
            'pending': 'Picking',
            'ready': 'Delivering',
            'confirmed': 'Delivered'
        }
        if not order_id:
            message = _('Order Id Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

        sale_order = request.env['sale.order'].sudo().browse(int(order_id))
        if not sale_order:
            message = _('Order not Found!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        else:
            ord_status = {}
            if sale_order.delivery_picking_id:
                ord_status = {'status_inf': delivery_state[sale_order.delivery_picking_id.state]
                              }
            else:
                ord_status = {'status_inf': 'Ready for Picking'
                              }

            message = _('Your Order Status')
            status = _('Success')
            result = {'status': status, 'message': message, 'order_status': ord_status}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/my_order_history',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def my_order_history(self, fields=None, context=None, **kw):
        ctx = request.session.context.copy()
        ctx.update(context and parse_value(context) or {})

        partner = kw.get('partner_id')
        if not partner:
            message = _('Customer Id Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])
        if not partner_id:
            message = _('Customer Not Found!')
            status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

        sale_order = request.env['sale.order'].sudo().search(
            [('partner_id', '=', int(partner)), ('order_placed', '=', True),
             ('delivery_picking_id.state', '=', 'confirmed'), ('cancelled_order', '=', False)])
        cancelleded_orders = request.env['sale.order'].sudo().search(
            [('partner_id', '=', int(partner)), ('order_placed', '=', True), ('cancelled_order', '=', True)])

        ids = ''
        # print(sale_order,"salee")
        results = []
        if sale_order or cancelleded_orders:

            for order in sale_order:
                # print(order,"saleorderrrr")
                product_list = []
                for line in order.order_line:
                    uom_vals = []
                    if line.product_id.product_uom_ids:
                        for product_uom in line.product_id.product_uom_ids:
                            uom_vals.append({
                                'uom': product_uom.uom_id.name,
                                'uom_id': product_uom.uom_id.id,
                                'quantity': product_uom.quantity,
                                'id': product_uom.id
                            })
                    # print(line,"line orders")

                    product_list.append({
                        'line_id': line.id,
                        'product_id': line.product_id.id,
                        'product': line.product_id.name if line.product_id else False,
                        'image': line.product_id.image_1920 if line.product_id else False,
                        'qty': line.product_uom_qty,
                        'is_delivery': True if line.is_delivery else False,
                        'price': line.price_unit,
                        'strike_price': line.product_id.mrp,
                        'product_set_uom': line.product_set_uom,
                        'ordered_qty': line.ordered_qty,
                        'is_service': True if line.product_id.type == 'service' else False,
                        # 'price_unit':line.price_unit,
                        # 'price_subtotal':line.price_subtotal,
                        'uom_name': uom_vals if line.product_id.product_uom_ids else False,
                        # 'date':line.order_id.delivery_picking_id.create_time,
                        'malayalam_name': line.product_id.malayalam_name

                    })
                results.append({
                    'order_number': order.name,
                    'date': order.create_date,
                    'partner_id': order.partner_id.name,
                    'products': product_list,
                    'location': order.company_id.id if order.company_id else False,
                    'is_cancelled': False,
                    'order_id': order.id
                })

            # results = []

            for order in cancelleded_orders:
                # print(order,"cancelledorderrrr")
                product_list = []
                for line in order.order_line:
                    uom_vals = []
                    if line.product_id.product_uom_ids:
                        for product_uom in line.product_id.product_uom_ids:
                            uom_vals.append({
                                'uom': product_uom.uom_id.name,
                                'uom_id': product_uom.uom_id.id,
                                'quantity': product_uom.quantity,
                                'id': product_uom.id
                            })
                    # print(line,"line orders")

                    product_list.append({
                        'line_id': line.id,
                        'product_id': line.product_id.id,
                        'product': line.product_id.name if line.product_id else False,
                        'image': line.product_id.image_1920 if line.product_id else False,
                        'qty': line.product_uom_qty,
                        'is_delivery': True if line.is_delivery else False,
                        'price': line.price_unit,
                        'strike_price': line.product_id.mrp,
                        'is_service': True if line.product_id.type == 'service' else False,
                        'ordered_qty': line.ordered_qty,
                        # 'price_unit':line.price_unit,
                        # 'price_subtotal':line.price_subtotal,
                        'product_set_uom': line.product_set_uom,
                        'uom_name': uom_vals if line.product_id.product_uom_ids else False,
                        # 'date':line.order_id.delivery_picking_id.create_time,
                        'malayalam_name': line.product_id.malayalam_name

                    })
                results.append({
                    'order_number': order.name,
                    'date': order.create_date,
                    'partner_id': order.partner_id.name,
                    'cancelled_products': product_list,
                    'location': order.company_id.id if order.company_id else False,
                    'is_cancelled': True,
                    'order_id': order.id
                })
                # print(product_list,"producttt_listtt")
            # results.append(order_details)
            # print("result",results)
            sorted_result = sorted(results, key=lambda i: i['order_id'], reverse=True)
            # print(sorted_result,"sorted")

            result = {'status': 'Success', 'message': 'Your Order History!', 'order_history': sorted_result}

        else:

            result = {'status': 'Failed', 'message': 'You have no delivered orders yet!'}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    # @http.route([
    #     '/api/sub_category/products/pagination',
    # ], auth="none", type='http', methods=['GET'])
    # @tools.common.parse_exception
    # @tools.common.ensure_database
    # @tools.common.ensure_module()
    # @tools.security.protected()
    # def products_pagination(self, **kw):
    #     category_id = kw.get('categ_id')
    #     page_number = kw.get('page_number')
    #     companys_id = kw.get('location_id')
    #
    #
    #     start = 0
    #     end = 0
    #     if not page_number or not category_id:
    #         if not page_number:
    #             message = _('Page Number Not Given!')
    #             status = _('Failed')
    #         if not category_id:
    #             message = _('Category Id Not Given!')
    #             status = _('Failed')
    #         result = {'status': status, 'message': message}
    #         content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
    #         return Response(content, content_type='application/json;charset=utf-8', status=200)
    #     if page_number:
    #         page_number = int(page_number)
    #         if page_number ==1:
    #             start =0
    #             end = 20
    #         else:
    #             start = (page_number -1) * 20
    #             end = start + 20
    #
    #     product_list = []
    #     filter_product = []
    #
    #
    #     products = request.env['product.product'].search([('categ_id.id', '=', category_id)])
    #     company_id = request.env['res.company'].sudo().search([('id', '=', int(companys_id))])
    #     if products:
    #         for product in products:
    #             images = []
    #             uom_vals = []
    #             if product.company_id:
    #                 if product.company_id == company_id:
    #                     if product.product_images_ids:
    #                         for product_image in product.product_images_ids:
    #                             images.append(product_image.image_000)
    #                     if product.product_uom_ids:
    #                         for product_uom in product.product_uom_ids:
    #                             uom_vals.append({
    #                                 'uom': product_uom.uom_id.name,
    #                                 'uom_id':product_uom.uom_id.id,
    #                                 'quantity':product_uom.quantity
    #                             })
    #
    #                     product_list.append({
    #                         'product_id': product.id,
    #                         'product': product.name,
    #                         'price': product.lst_price,
    #                         'strike_price': product.mrp,
    #                         'image': product.image_1920,
    #                         'currency': product.currency_id.name,
    #                         'qty_available': product.qty_available,
    #                         'uom_name': uom_vals if product.product_uom_ids else False ,
    #                         'category_id': product.categ_id.id if product.categ_id else False,
    #                         'image_list': images if product.product_images_ids else False,
    #                         'malayalam_name':product.malayalam_name,
    #                         'description': product.description_sale,
    #                         'location': product.company_id.name if product.company_id else False,
    #                         'has_offer': True if product.is_offer else False
    #
    #                     })
    #             else:
    #                 if product.product_images_ids:
    #                     for product_image in product.product_images_ids:
    #                         images.append(product_image.image_000)
    #                 if product.product_uom_ids:
    #                     for product_uom in product.product_uom_ids:
    #                         uom_vals.append({
    #                             'uom': product_uom.uom_id.name,
    #                             'uom_id': product_uom.uom_id.id,
    #                             'quantity': product_uom.quantity
    #                         })
    #
    #                 product_list.append({
    #                     'product_id': product.id,
    #                     'product': product.name,
    #                     'price': product.lst_price,
    #                     'strike_price': product.mrp,
    #                     'image': product.image_1920,
    #                     'currency': product.currency_id.name,
    #                     'qty_available': product.qty_available,
    #                     'uom_name': uom_vals if product.product_uom_ids else False,
    #                     'category_id': product.categ_id.id if product.categ_id else False,
    #                     'image_list': images if product.product_images_ids else False,
    #                     'malayalam_name': product.malayalam_name,
    #                     'description': product.description_sale,
    #                     'location':product.company_id.name if product.company_id else False,
    #                     'has_offer': True if product.is_offer else False
    #
    #                 })
    #
    #         if len(product_list)-1 < start :
    #             result = {'status': 'Failed', 'message': 'No products in this Page!'}
    #         else:
    #             if len(product_list) < end:
    #                 for i in range(start, len(product_list)):
    #                     filter_product.append(product_list[i])
    #             else:
    #                 for i in range(start,end):
    #                     filter_product.append(product_list[i])
    #             result = {'status': 'Success', 'product_values': filter_product}
    #     else:
    #         result = {'status': 'Success', 'message': 'No products under this categroy!',
    #                   'product_values': product_list}
    #
    #     content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
    #     return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route(['/api/sub_category/products/pagination', ], auth="none", type='http', methods=['GET'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def products_pagination(self, **kw):
        category_id = kw.get('categ_id')
        page_number = kw.get('page_number')
        companys_id = kw.get('location_id')
        start = end = 0

        if not page_number:
            message = _('Page Number Not Given!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if page_number:
            page_number = int(page_number)
            if page_number == 1:
                start = 0
                end = 20
            else:
                start = (page_number - 1) * 20
                end = start + 20
        filter_product = []
        company_id = request.env['res.company'].sudo().browse(int(companys_id))
        products = request.env['product.product'].sudo().search_read(['|', ('company_id', '=', False),
                                                                      ('company_id', '=', company_id.id),
                                                                      ('categ_id.id', '=', category_id),
                                                                      ('show_in_app', '=', True)],
                                                                     ['id', 'name', 'list_price', 'mrp',
                                                                      'malayalam_name', 'image_256', 'display_uom',
                                                                      'categ_id', 'is_offer', 'uom_id'],
                                                                     order='sequence')
        # print(products,"products")

        if products:

            if len(products) - 1 < start:
                result = {'status': 'Failed', 'message': 'No products in this Page!'}
            else:
                if len(products) < end:
                    filter_product = products[start:len(products)]
                else:
                    filter_product = products[start:end]
                result = {'status': 'Success', 'product_values': filter_product}
        else:
            result = {'status': 'Success', 'message': 'No products under this categroy!',
                      'product_values': filter_product}

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/location',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def location(self, **kw):
        location_ids = request.env['res.company'].search([])
        locations = []
        if location_ids:
            for location in location_ids:
                locations.append({
                    'id': location.id,
                    'location': location.name
                })
            result = {'status': 'Success', 'location_vals': locations}
        else:
            result = {'status': 'Failed', 'location_vals': locations}

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/get/delivery_methods'
    ], auth="none", type='http', methods=['GET'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def get_delivery_method(self, **kw):
        company_id = kw.get('location_id')

        delivery_methods = request.env['delivery.carrier'].search([('company_id', '=', int(company_id))])
        delivry_methods = []
        if delivery_methods:

            for method in delivery_methods:

                if not method.scheduled_delivery:
                    delivry_methods.append({
                        'id': method.id,
                        'delivery_method': method.name,
                        'estimated_time': method.delivery_time

                    })
                else:
                    time_slots_list = []
                    time_slots = request.env['delivery.time.slot'].search([])
                    for time_slot in time_slots:
                        time_slots_list.append({
                            'from_time': time_slot.from_time,
                            'to_time': time_slot.to_time,
                            'am/pm': time_slot.timing,
                            'id': time_slot.id
                        })

                    delivry_methods.append({
                        'id': method.id,
                        'delivery_method': method.name,
                        'time_slot': time_slots_list,
                        'is_scheduled': True if method.scheduled_delivery else False
                    })

            result = {'status': 'Success', 'delivry_method_vals': delivry_methods}
        else:
            result = {'status': 'Failed', 'delivry_method_vals': delivry_methods}

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/get/upi_details',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def upi_details(self, **kw):
        company_id = kw.get('location_id')
        company = request.env['res.company'].sudo().search([('id', '=', int(company_id))])
        if not company_id:
            message = _('Please provide location!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if not company:
            message = _('No such location found!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        else:
            message = _('UPI details for the selected location!')
            status = _('Success')
            upi_details = {'upi_id': company.upi_id, 'merchant_id': company.mechant_id, 'name': company.person_name}
            result = {'status': status, 'message': message, 'upi_vals': upi_details}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/selected_location'

    ], auth="none", type='http', methods=['GET'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def get_location(self, **kw):
        partner_id = kw.get('partner_id')
        partner_record = request.env['res.partner'].search([('id', '=', int(partner_id))])
        selected_location = {}

        if partner_record:
            selected_location = {
                'branch_id': partner_record.company_id.id if partner_record.company_id else False,
                'branch_name': partner_record.company_id.name if partner_record.company_id else False,

            }
            result = {'status': 'Success', 'branch_details': selected_location}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        else:
            result = {'status': 'Failed', 'message': 'No branches set!', 'branch_details': selected_location}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/banners',

    ], auth="none", type='http', methods=['GET'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def get_selected_location(self, **kw):
        location_id = kw.get('location')
        if not kw.get('location'):
            message = _('Specify the location!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

        company = request.env['res.company'].sudo().search([('id', '=', int(location_id))])

        selected_location = {}

        if company:
            banner_images = []
            banner_details = []
            if company.banner_images_ids:
                for banner in company.banner_images_ids:
                    if banner.is_active:
                        banner_details.append({
                            'category': banner.category_id.id if banner.category_id else False,
                            'banner_images': banner.banner_image
                        })

                result = {'status': 'Success', 'banner_images': banner_details}
                content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                return Response(content, content_type='application/json;charset=utf-8', status=200)
            else:
                result = {'status': 'Failed', 'message': 'Please add some banner images in your branch',
                          'banner_images': banner_images}
                content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                return Response(content, content_type='application/json;charset=utf-8', status=200)

        else:
            result = {'status': 'Failed', 'message': 'No location found!'}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/change/selected_location',

    ], auth="none", type='http', methods=['PUT'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['write'])
    def change_selected_location(self, **kw):
        partner_id = kw.get('partner_id')
        company_id = kw.get('location_id')
        partner_record = request.env['res.partner'].sudo().search([('id', '=', int(partner_id))])
        company = request.env['res.company'].sudo().search([('id', '=', int(company_id))])
        user_id = request.env['res.users'].sudo().search([('partner_id', '=', partner_record.id)])
        selected_location = {}

        if user_id:

            user_id.write({
                'company_id': company.id
            })

            result = {'status': 'Success', 'message': 'Location Updated'}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        else:
            result = {'status': 'Failed', 'message': 'No such partner'}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/delivery_method'
    ], auth="none", type='http', methods=['PUT'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected(operations=['create'])
    def delivery_method(self, **kw):
        partner = kw.get('partner_id')
        companys_id = kw.get('location_id')
        partner_id = request.env['res.partner'].sudo().search([('id', '=', int(partner))])
        company_id = request.env['res.company'].sudo().search([('id', '=', int(companys_id))])
        if not kw.get('delivery_method'):
            message = _('Specify the delivery method!')
            status = _('Failed')
            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        else:
            delivery_method = kw.get('delivery_method')
            time_slot = kw.get('time_slot')
            delivery_methods = request.env['delivery.carrier'].sudo().search([('id', '=', int(delivery_method))])
            existing_sale_order_line = ''
            sale_order_line = ''
            sale_order = request.env['sale.order'].sudo().search(
                [('partner_id', '=', int(partner)), ('state', '=', 'draft'), ('order_placed', '=', False),
                 ('company_id', '=', company_id.id)], limit=1)
            if not delivery_methods.scheduled_delivery:
                if sale_order:
                    sale_order.write({
                        'carrier_id': delivery_methods.id,
                        'partner_shipping_id': partner_id.id,
                        'partner_invoice_id': partner_id.id,

                    })
                    total_amount = sale_order.amount_total
                    delivery_charge = ''
                    rate = {}
                    if delivery_methods.delivery_type in ('fixed', 'base_on_rule'):
                        carrier_price = 1
                        if delivery_methods.free_over:
                            if delivery_methods.amount > 0:
                                if total_amount > delivery_methods.amount:
                                    carrier_price = 0
                        if carrier_price == 0:
                            delivery_charge = 0.0
                        else:
                            rate = delivery_methods.rate_shipment(sale_order)
                            if rate:
                                delivery_charge = rate.get('carrier_price')

                    message = _('Updated the delivery method!')
                    status = _('Success')
                    result = {'status': status, 'message': message, 'delivery_charge': delivery_charge}
                    content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                    return Response(content, content_type='application/json;charset=utf-8', status=200)
                else:
                    message = _('Please add some items to cart!')
                    status = _('Failed')
                    result = {'status': status, 'message': message}
                    content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                    return Response(content, content_type='application/json;charset=utf-8', status=200)
            else:
                if not time_slot:
                    message = _('Please provide the time slot!')
                    status = _('Failed')
                    result = {'status': status, 'message': message}
                    content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                    return Response(content, content_type='application/json;charset=utf-8', status=200)
                else:
                    if sale_order:
                        sale_order.write({
                            'carrier_id': delivery_methods.id,
                            'delivery_time_slots': time_slot,
                            'partner_shipping_id': partner_id.id,
                            'partner_invoice_id': partner_id.id,

                        })
                        total_amount = sale_order.amount_total
                        delivery_charge = ''
                        rate = {}
                        if delivery_methods.delivery_type in ('fixed', 'base_on_rule'):
                            carrier_price = 1
                            if delivery_methods.free_over:
                                if delivery_methods.amount > 0:
                                    if total_amount > delivery_methods.amount:
                                        carrier_price = 0
                            if carrier_price == 0:
                                delivery_charge = 0.0
                            else:
                                rate = delivery_methods.rate_shipment(sale_order)
                                if rate:
                                    delivery_charge = rate.get('carrier_price')
                        message = _('Updated the scheduled delivery!')
                        status = _('Success')
                        result = {'status': status, 'message': message, 'delivery_charge': delivery_charge}
                        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/user/search_products',

    ], auth="none", type='http', methods=['GET'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def user_search(self, **kw):
        keyword = kw.get('keywords')
        companys_id = kw.get('location_id')
        page_number = kw.get('page_number')

        start = 0
        end = 0
        if not page_number:
            message = _('Page Number Not Given!')
            status = _('Failed')

            result = {'status': status, 'message': message}
            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if page_number:
            page_number = int(page_number)
            if page_number == 1:
                start = 0
                end = 20
            else:
                start = (page_number - 1) * 20
                end = start + 20

        filter_product = []
        company_id = request.env['res.company'].sudo().browse(int(companys_id))

        products = request.env['product.product'].sudo().search_read(['|', ('company_id', '=', False),
                                                                      ('company_id', '=', company_id.id), '|',
                                                                      ('product_tag_ids.name', 'ilike', keyword),
                                                                      ('name', 'ilike', keyword),
                                                                      ('show_in_app', '=', True)],
                                                                     ['id', 'name', 'list_price', 'mrp',
                                                                      'malayalam_name', 'image_256', 'display_uom',
                                                                      'categ_id', 'is_offer', 'uom_id'],
                                                                     order="name asc")

        if products:

            if len(products) - 1 < start:
                result = {'status': 'Failed', 'message': 'No products in this Page!'}
            else:
                if len(products) < end:
                    filter_product = products[start:len(products)]
                else:
                    filter_product = products[start:end]
                result = {'status': 'Success', 'product_values': filter_product}
        else:

            result = {'status': 'Success', 'message': 'No products under this categroy!',
                      'product_values': filter_product}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route([
        '/api/get_app_version',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def get_app_version(self, fields=None, **kw):
        version = request.env["ir.config_parameter"].sudo().get_param("odx_delivery_customization.latest_app_version")
        result = version
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    ###############################################################
    # Delivery App APIS
    ################################################################

    @http.route([
        '/api/delivery/get/notification/counts',
    ], auth="none", type='http', methods=['GET'])
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.security.protected()
    def get_notification_counts(self, **kw):
        data = json.loads(request.httprequest.data)
        uid = int(data.get('user_id'))
        user = request.env['res.users'].browse(uid)
        partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
        if user.company_id:
            company_id = user.company_id.id
        work_details = request.env['work.details'].search(
            [('picking_boy_id', '=', partner.id), ('state', '=', 'done'), ('company_id', '=', company_id)],
            order='id desc', limit=1)
        no_of_pickings = 0
        no_of_deliveries = 0
        ready_to_picking = []
        ready_to_delivery = []
        if work_details.picking_ids:
            for picking in work_details.picking_ids:
                if picking.state == 'pending' and picking.pick_up_boy_id.id == work_details.id:
                    ready_to_picking.append(picking)
            no_of_pickings = len(ready_to_picking)
        if work_details.delivery_ids:
            for delivery in work_details.delivery_ids:
                if delivery.state == 'ready' and delivery.delivery_boys_id.id == work_details.id:
                    ready_to_delivery.append(delivery)
            no_of_deliveries = len(ready_to_delivery)
        data = {'ready_to_pickup': no_of_pickings, 'ready_to_delivery': no_of_deliveries}
        result = {'status': 'ok', 'message': 'success', 'data': data}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    #
    # @http.route([
    #     '/api/delivery/sign_in'
    # ], auth="none", type='http', methods=['POST'], csrf=_csrf)
    # @tools.common.parse_exception
    # @tools.common.ensure_database
    # @tools.common.ensure_module()
    # @tools.security.protected(operations=['create'])
    # def delivery_sign_up(self, values=None, context=None, **kw):
    #     ctx = request.session.context.copy()
    #     ctx.update(context and parse_value(context) or {})
    #     partner_values = {}
    #     result = {}
    #     user_group_portal = request.env.ref('base.group_user')
    #     phone_code = kw.get('phone_code')
    #     countrys_id = request.env['res.country'].search([('phone_code', '=', phone_code)], limit=1)
    #     # print(countrys_id.name)
    #
    #     companies = request.env['res.company'].search([])
    #     company_list = []
    #     for company in companies:
    #         company_list.append(company)
    #     groups = {
    #         'groups_id': [(6, 0, [user_group_portal.id])],
    #         'company_ids': [(6, 0, [company.id for company in company_list])],
    #         'country_id': countrys_id.id
    #     }
    #
    #     values = values and parse_value(values) or {}
    #     values.update(groups)
    #
    #     model = request.env['res.users'].with_context(ctx)
    #     # print(values,"vals")
    #     user = request.env['res.users'].search([('login', '=', values.get('login'))])
    #     # print(user.name,"username")
    #     message = ''
    #     status = ''
    #
    #     if not user:
    #         if not values.get('login'):
    #             message = _('Please provide mobile number!')
    #             status = _('Failed')
    #         elif not values.get('password'):
    #             message = _('Please set a password!')
    #             status = _('Failed')
    #         elif not values.get('name'):
    #             message = _('Please provide your name!')
    #             status = _('Failed')
    #         elif not values.get('company_id'):
    #             message = _('Please provide location!')
    #             status = _('Failed')
    #         else:
    #
    #             message = _('Successful! Enjoy Shopping!!')
    #             status = _('Success')
    #
    #             user_id = model.sudo().create(values)
    #             # if user_id:
    #             #     vals = {
    #             #         'name':'client api',
    #             #         'state': 'client_credentials',
    #             #         'security': 'basic',
    #             #         'user':user_id.id
    #             #
    #             #     }
    #             #     token_id = request.env['muk_rest.oauth2'].create(vals)
    #
    #             partner = request.env['res.partner'].search([('id', '=', user_id.partner_id.id)])
    #             if partner:
    #                 partner.company_id = user_id.company_id.id
    #             partner_values = {'id': partner.id, 'name': partner.name, 'mobile': partner.mobile,
    #                               'location': partner.city, 'selected_location': partner.company_id.name
    #                               }
    #             result.update(partner_values)
    #
    #         result = {'status': status, 'message': message, 'partner_details': partner_values}
    #
    #         # print(result, "usercerar")
    #
    #
    #     else:
    #         result = {'status': 'Failed', 'message': _('Already existing customer!'),
    #                   }
    #
    #     content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
    #     return Response(content, content_type='application/json;charset=utf-8', status=200)
