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
import json
import urllib
import logging
import random as r

from werkzeug import exceptions, utils
from odoo.exceptions import ValidationError

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi

from odoo import _, http
from odoo.http import request, Response
# from odoo.exceptions import AccessDenied
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.tools import misc, config

from odoo.addons.muk_rest import validators, tools
from odoo.addons.muk_utils.tools.json import ResponseEncoder, RecordEncoder

_logger = logging.getLogger(__name__)
_csrf = config.get('rest_csrf', False)


class AuthenticationController(http.Controller):

    def __init__(self):
        super(AuthenticationController, self).__init__()
        self.oauth1 = validators.oauth1_provider
        self.oauth2 = validators.oauth2_provider

    # ----------------------------------------------------------
    # OAuth Authorize
    # ----------------------------------------------------------

    def client_information(self, client, values={}):
        values.update({
            'name': client.homepage,
            'company': client.company,
            'homepage': client.homepage,
            'logo_url': client.logo_url,
            'privacy_policy': client.privacy_policy,
            'service_terms': client.service_terms,
            'description': client.description,
        })
        return values

    def oauth1_information(self, token, realms=[], values={}):
        model = request.env['muk_rest.request_token'].sudo()
        domain = [('resource_owner_key', '=', token)]
        request_token = model.search(domain, limit=1)
        if token and request_token.exists():
            values = self.client_information(request_token.oauth, values)
            values.update({
                'oauth_token': request_token.resource_owner_key,
                'callback': request_token.callback,
                'realms': realms or [],
            })
            return values
        else:
            raise exceptions.BadRequest

    def oauth2_information(self, client_id, redirect_uri, response_type, state=None, scopes=[], values={}):
        model = request.env['muk_rest.oauth2'].sudo()
        domain = [('client_id', '=', client_id)]
        oauth = model.search(domain, limit=1)
        if client_id and redirect_uri and response_type and oauth.exists():
            values = self.client_information(oauth, values)
            values.update({
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'response_type': response_type,
                'state': state,
                'scopes': scopes or []
            })
            return values
        else:
            raise exceptions.BadRequest

    # ----------------------------------------------------------
    # OAuth 1.0
    # ----------------------------------------------------------

    @http.route('/api/authentication/oauth1/initiate', auth="none", type='http', methods=['POST'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.common.ensure_import()
    def oauth1_initiate(self, **kw):
        headers, body, status = self.oauth1.create_request_token_response(
            uri=request.httprequest.url,
            http_method=request.httprequest.method,
            body=request.httprequest.form,
            headers=request.httprequest.headers)
        return Response(response=body, headers=headers, status=status)

    @http.route('/api/authentication/oauth1/authorize', auth="none", type='http', methods=['GET', 'POST'], csrf=_csrf)
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.common.ensure_import()
    def oauth1_authorize(self, **kw):
        try:
            if request.httprequest.method.upper() == 'GET':
                realms, credentials = self.oauth1.get_realms_and_credentials(
                    uri=request.httprequest.url,
                    http_method=request.httprequest.method,
                    body=request.httprequest.form,
                    headers=request.httprequest.headers)
                resource_owner_key = credentials.get('resource_owner_key', False)
                values = self.oauth1_information(resource_owner_key, realms)
                return request.render('muk_rest.authorize_oauth1', values)
            elif request.httprequest.method.upper() == 'POST':
                login = request.params.get('login', None)
                password = request.params.get('password', None)
                token = request.params.get('oauth_token')
                realms = request.httprequest.form.getlist('realms')
                try:
                    uid = request.session.authenticate(request.env.cr.dbname, login, password)
                    headers, body, status = self.oauth1.create_authorization_response(
                        uri=request.httprequest.url,
                        http_method=request.httprequest.method,
                        body=request.httprequest.form,
                        headers=request.httprequest.headers,
                        realms=realms or [],
                        credentials={'user': uid})
                    if status == 200:
                        verifier = str(urllib.parse.parse_qs(body)['oauth_verifier'][0])
                        content = json.dumps({'oauth_token': token, 'oauth_verifier': verifier}, sort_keys=True,
                                             indent=4)
                        return Response(content, content_type='application/json;charset=utf-8', status=200)
                    else:
                        return Response(body, status=status, headers=headers)
                except AccessDenied:
                    values = self.oauth1_information(token, realms)
                    values.update({'error': _("Invalid login or password!")})
                    return request.render('muk_rest.authorize_oauth1', values)
        except exceptions.HTTPException as exc:
            _logger.exception("OAUth authorize failed!")
            return utils.redirect('/api/authentication/error', 302, exc)
        except:
            _logger.exception("OAUth authorize")
            return utils.redirect('/api/authentication/error', 302)

    @http.route('/api/authentication/oauth1/token', auth="none", type='http', methods=['POST'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.common.ensure_import()
    def oauth1_token(self, **kw):
        headers, body, status = self.oauth1.create_access_token_response(
            uri=request.httprequest.url,
            http_method=request.httprequest.method,
            body=request.httprequest.form,
            headers=request.httprequest.headers)
        return Response(response=body, headers=headers, status=status)

        # ----------------------------------------------------------

    # OAuth 2.0
    # ----------------------------------------------------------
    #
    # @http.route('/api/delivery/login', auth="none", type='json', methods=['GET', 'POST'], csrf=_csrf)
    # @tools.common.ensure_database
    # @tools.common.ensure_module()
    # @tools.common.ensure_import()
    # def delivery_login_authorize(self, **kw):
    #         if request.httprequest.method.upper() == 'POST':
    #
    #             login = request.params.get('user_name', None)
    #             password = request.params.get('password', None)
    #
    #             # client_id = request.params.get('client_id')
    #             # scopes = request.httprequest.form.getlist('scopes')
    #             try:
    #                 uid = request.session.authenticate(request.env.cr.dbname, login, password)
    #                 print(uid,"userrrrrr")
    #
    #                 if uid:
    #                     print("heeeeeeeeeee")
    #                     user = request.env['res.users'].search([('id', '=', uid)])
    #                     print(user,"userrrrrrrrrr")
    #                     partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
    #                     partner_values = { 'name': partner.name,
    #                                       'user_id':user.id
    #                                       }
    #                     result = {'status': 'ok', 'message': _('Successfully logged in!'),'data':partner_values
    #                           }
    #
    #                     return result
    #                 else:
    #                     partner_values = {'code': 404,
    #                                       'details': 'null',
    #                                       'message': _('User not Found!')
    #                                       }
    #                     result = {'status': 'nok',  'error': partner_values}
    #             except UserError as e:
    #                 msg = e.name
    #             except AccessDenied as e:
    #                 msg = e.args[0]
    #             if msg == AccessDenied().args[0]:
    #                 msg = _('Invalid Username or Password!')
    #                 result = {'status': 'Failed', 'message': msg
    #                           }
    #                 content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
    #                 return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route('/api/login', auth="none", type='http', methods=['GET', 'POST'], csrf=_csrf)
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.common.ensure_import()
    def login_authorize(self, **kw):

        if request.httprequest.method.upper() == 'POST':
            login = request.params.get('login', None)
            password = request.params.get('password', None)
            # client_id = request.params.get('client_id')
            # scopes = request.httprequest.form.getlist('scopes')
            try:
                uid = request.session.authenticate(request.env.cr.dbname, login, password)
                # print(uid,"userrrrrr")

                if uid:
                    user = request.env['res.users'].search([('id', '=', uid)])
                    partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
                    partner_values = {'partner_id': partner.id, 'name': partner.name, 'mobile': partner.mobile,
                                      'location': partner.city, 'user_id': user.id, 'ukka_coins': partner.loyalty_points
                                      }
                    result = {'status': 'Success', 'message': _('Successfully logged in!'), 'user': partner_values
                              }
                    content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                    return Response(content, content_type='application/json;charset=utf-8', status=200)
            except UserError as e:
                msg = e.name
            except AccessDenied as e:
                msg = e.args[0]
            if msg == AccessDenied().args[0]:
                msg = _('Invalid Username or Password!')
                result = {'status': 'Failed', 'message': msg
                          }
                content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
                return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route('/api/authentication/oauth2/authorize', auth="none", type='http', methods=['GET', 'POST'], csrf=_csrf)
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.common.ensure_import()
    def oauth2_authorize(self, **kw):
        try:
            if request.httprequest.method.upper() == 'GET':
                scopes, credentials = self.oauth2.validate_authorization_request(
                    uri=request.httprequest.url,
                    http_method=request.httprequest.method,
                    body=request.httprequest.form,
                    headers=request.httprequest.headers)
                client_id = credentials.get('client_id', False)
                redirect_uri = credentials.get('redirect_uri', False)
                response_type = credentials.get('response_type', False)
                state = credentials.get('state', False)
                values = self.oauth2_information(client_id, redirect_uri, response_type, state, scopes)
                return request.render('muk_rest.authorize_oauth2', values)
            elif request.httprequest.method.upper() == 'POST':
                login = request.params.get('login', None)
                password = request.params.get('password', None)
                client_id = request.params.get('client_id')
                redirect_uri = request.params.get('redirect_uri')
                response_type = request.params.get('response_type')
                state = request.params.get('state')
                scopes = request.httprequest.form.getlist('scopes')
                try:
                    uid = request.session.authenticate(request.env.cr.dbname, login, password)
                    headers, body, status = self.oauth2.create_authorization_response(
                        uri=request.httprequest.url,
                        http_method=request.httprequest.method,
                        body=request.httprequest.form,
                        headers=request.httprequest.headers,
                        scopes=scopes or ['all'],
                        credentials={'user': uid})
                    return Response(body, status=status, headers=headers)
                except AccessDenied:
                    values = self.oauth2_information(client_id, redirect_uri, response_type, state, scopes)
                    values.update({'error': _("Invalid login or password!")})
                    return request.render('muk_rest.authorize_oauth2', values)
        except exceptions.HTTPException as exc:
            _logger.exception("OAUth authorize")
            return utils.redirect('/api/authentication/error', 302, exc)
        except:
            _logger.exception("OAUth authorize")
            return utils.redirect('/api/authentication/error', 302)

    @http.route('/api/forget_password', type='http', auth="none", methods=['GET'], csrf=_csrf)
    def forget_password(self, **kw):
        login = kw.get('mobile')
        user_id = request.env['res.users'].sudo().search([('login', '=', login)])
        if user_id:
            otp = ""
            for i in range(4):
                otp += str(r.randint(1, 9))
            otp_values = {
                'msg': 'Your OTP is',
                'OTP': otp
            }
            record = request.env['gateway_setup'].sudo().search([], limit=1)
            mobile = '+' + kw.get('mobile')
            record.update({
                'mobile': mobile,
                'message': otp,
            })

            try:
                record.sms_test_action()
            except:
                pass

            result = {'status': 'Success', 'Otp_vals': otp_values}
        else:
            result = {'status': 'Failed', 'message': 'Please provide the mobile number you have registered with us!'}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route('/api/change_password', type='http', auth="none", methods=['POST'], csrf=_csrf)
    def change_password(self, **kw):
        login = kw.get('mobile')
        new_password = kw.get('new_password')
        confirm_password = kw.get('confirm_password')
        user_id = request.env['res.users'].sudo().search([('login', '=', login)])
        if not (new_password.strip() and confirm_password.strip()):
            result = {'status': 'Failed', 'message': _('You cannot leave any password empty.')}

            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if new_password != confirm_password:
            result = {'status': 'Failed', 'message': _('The new password and its confirmation must be identical.')}

            content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
            return Response(content, content_type='application/json;charset=utf-8', status=200)
        if user_id:
            if new_password == confirm_password:
                user_id.write({
                    'password': new_password
                })
            status = 'Success',
            message = _('Your password has been updated!')
        else:
            status = 'Success',
            message = _('Please check the mobile number you have registered with us!')

        # except UserError as e:
        #     message = e.name
        result = {'status': status, 'message': message}

        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route('/api/authentication/oauth2/token', auth="none", type='http', methods=['POST'], csrf=False)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.common.ensure_import()
    def oauth2_token(self, **kw):
        headers, body, status = self.oauth2.create_token_response(
            uri=request.httprequest.url,
            http_method=request.httprequest.method,
            body=request.httprequest.form,
            headers=request.httprequest.headers)

        return Response(response=body, headers=headers, status=status)

    ######################################
    # DELIVERY APP AUTHENTICATION API
    ######################################

    @http.route('/api/delivery/authentication', auth="none", type='json', methods=['POST'], csrf=False)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.common.ensure_import()
    def delivery_authentication(self, *args, **kw):
        data = json.loads(request.httprequest.data)
        headers, body, status = self.oauth2.create_token_response(
            uri=request.httprequest.url,
            http_method=request.httprequest.method,
            body=json.loads(request.httprequest.data),
            headers=request.httprequest.headers)
        access_token = json.loads(body)
        if request.httprequest.method.upper() == 'POST':
            login = data.get('user_name', None)
            password = data.get('password', None)
            try:
                uid = request.session.authenticate(request.env.cr.dbname, login, password)
                if uid:
                    user = request.env['res.users'].search([('id', '=', uid)])
                    partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
                    partner_values = {'name': partner.name,
                                      'user_id': user.id,
                                      'token': access_token.get('access_token')

                                      }
                    result = {'status': 'ok', 'message': _('Successfully logged in!'), 'data': partner_values
                              }

                    return result

            except UserError as e:
                msg = e.name

            except AccessDenied as e:
                msg = e.args[0]

            if msg == AccessDenied().args[0]:
                partner_values = {'code': 404,
                                  'details': 'null',
                                  'message': _('User not Found!')
                                  }

                result = {'status': 'nok', 'error': partner_values}
                return result

    @http.route('/api/authentication/oauth2/revoke', auth="none", type='http', methods=['POST'], csrf=_csrf)
    @tools.common.parse_exception
    @tools.common.ensure_database
    @tools.common.ensure_module()
    @tools.common.ensure_import()
    def oauth2_revoke(self, **kw):
        headers, body, status = self.oauth2.create_revocation_response(
            uri=request.httprequest.url,
            http_method=request.httprequest.method,
            body=request.httprequest.form,
            headers=request.httprequest.headers)
        request.session.logout()
        return Response(response=body, headers=headers, status=status)

    @http.route('/api/session/logout', type='http', auth="none", methods=['POST'], csrf=False)
    def logout(self):
        request.session.logout(keep_db=True)
        result = {'status': 'Success', 'message': 'Successfully logged out!!'}
        content = json.dumps(result, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route('/api/authentication/error', auth="none", type='http', methods=['GET'])
    def oauth_error(self, **kw):
        return request.render('muk_rest.authorize_error')
