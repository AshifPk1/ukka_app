# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast
from odoo import fields, models, api, _
from odoo.exceptions import UserError



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    earned_points = fields.Float(string="Earned Coins")
    earned_coin_value = fields.Float(string="Coin_Values")
    redeemed_coins = fields.Float(string="Redeemed Coins")
    redeemed_value = fields.Float(string="Redeemed Value")

    def check_loyalty_program(self):
        # print("helloooo")
        get_param = self.env['ir.config_parameter'].sudo().get_param
        activity_loyalty = get_param('odx_sales_loyalty.activate_loyalty')

        if activity_loyalty:
            loyalty_id = get_param('odx_sales_loyalty.loyalty_id')
            if not loyalty_id:
                raise UserError(_("Please configure a loyalty program in settings."))
            loyalty_id = ast.literal_eval(loyalty_id)
            loyalty_id = self.env["sale.loyalty.program"].search([('id', '=', loyalty_id)], limit=1)
            qty=0
            currency_loyalty = 0
            product_loyalty = 0
            pp_currency= loyalty_id.pp_currency
            pp_order = loyalty_id.pp_order
            pp_product = loyalty_id.pp_product
            total_loyalty =0
            for line in self.order_line:
                qty += line.product_uom_qty
                per_currency = pp_currency
                per_product = pp_product
                for rule in loyalty_id.rule_ids:
                    if rule.rule_type == 'product':
                        if line.product_id == rule.product_id:
                            per_currency = rule.pp_currency
                            per_product = rule.pp_product
                product_loyalty += per_product * line.product_uom_qty
                currency_loyalty += per_currency * line.price_subtotal
            total_loyalty = product_loyalty + currency_loyalty + pp_order
            self.earned_points = round(total_loyalty)
            # print(total_loyalty,"total_loyals")
            self.partner_id.loyalty_points += round(total_loyalty)
            # print(self.partner_id.loyalty_points,"partner loyals")

    def redeem_loyalty_points(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        activity_loyalty = get_param('odx_sales_loyalty.activate_loyalty')
        if activity_loyalty:
            loyalty_id = get_param('odx_sales_loyalty.loyalty_id')
            if not loyalty_id:
                raise UserError(_("Please configure a loyalty program in settings."))
            loyalty_id = ast.literal_eval(loyalty_id)
            loyalty_id = self.env["sale.loyalty.program"].search([('id', '=', loyalty_id)], limit=1)
            minimum_points = loyalty_id.minimum_points
            # discount_product = self.env['product.product'].search([('id','=',loyalty_id.disc_product_id.id)],limit=1)
            # discount_product = loyalty_id.disc_product_id.id if loyalty_id.disc_product_id else False
            balance_loyalty_points = self.partner_id.loyalty_points
            coin_value = 0
            if minimum_points:
                if self.partner_id.loyalty_points >= minimum_points:

                    redeem_amt = self.partner_id.loyalty_points * loyalty_id.point_amount
                    if redeem_amt < self.amount_total:
                        coin_value = redeem_amt
                    else:
                        coin_value = self.amount_total
                    redeemed_points = round(coin_value / loyalty_id.point_amount)
                    self.redeemed_coins = redeemed_points
                    self.redeemed_value = round(coin_value)

                    # if self.order_line:
                    #
                    #     redeem_line = self.order_line.create({
                    #         'order_id': self.id,
                    #         'name': loyalty_id.disc_product_id.name,
                    #         'product_uom_qty': 1,
                    #         'product_uom': loyalty_id.disc_product_id.uom_id.id,
                    #         'product_id': loyalty_id.disc_product_id.id,
                    #         'price_unit': -1 * round(coin_value),
                    #         'tax_id': False,
                    #         'ordered_qty':1
                    #
                    #
                    #     })

                        # if redeem_line:
                        #
                        #     redeemed_points = round(coin_value / loyalty_id.point_amount)
                        #     self.redeemed_coins = redeemed_points
                        #     self.redeemed_value = round(coin_value)
                        #
                        #     balance_loyalty_points = self.partner_id.loyalty_points - redeemed_points
                        #
                        #     self.partner_id.loyalty_points = balance_loyalty_points

                            # print(self.partner_id.loyalty_points,"customer louals")
                    delivery_charge = ''
                    rate = {}
                    if self.carrier_id.delivery_type in ('fixed', 'base_on_rule'):
                        rate = self.carrier_id.rate_shipment(self)
                    if rate:
                        delivery_charge = rate.get('price')
                    return {
                        'status': 'Success',
                        'message': _('Congratulations!You will gain a discount equal to coin value!') ,
                        'coin_value': -1 * round(coin_value),
                        'delivery_charge':delivery_charge,
                        'minimum_point': minimum_points,
                        'order_id': self.id,
                        'balance_ukka_coins': self.partner_id.loyalty_points - redeemed_points

                    }
                else:
                    delivery_charge = ''
                    rate = {}
                    if self.carrier_id.delivery_type in ('fixed', 'base_on_rule'):
                        rate = self.carrier_id.rate_shipment(self)
                    if rate:
                        delivery_charge = rate.get('price')
                    return {
                    'status': 'Success',
                    'message': 'Your coins is less than desired minimum coins!',
                    'order_id': self.id,
                    'delivery_charge':delivery_charge,
                    'balance_ukka_coins': self.partner_id.loyalty_points,
                    'coin_value':0
                    }

    def points_in_canceled_order(self):
        if self.cancelled_order:
            balance_coins = self.partner_id.loyalty_points - self.earned_points + self.redeemed_coins
            self.partner_id.loyalty_points = balance_coins

    # add redeem line in sale order line
    def add_redeem_line(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        activity_loyalty = get_param('odx_sales_loyalty.activate_loyalty')
        if activity_loyalty:
            loyalty_id = get_param('odx_sales_loyalty.loyalty_id')
            if not loyalty_id:
                raise UserError(_("Please configure a loyalty program in settings."))
            loyalty_id = ast.literal_eval(loyalty_id)
            loyalty_id = self.env["sale.loyalty.program"].search([('id', '=', loyalty_id)], limit=1)

            if self.redeemed_value > 0:

                redeem_line = self.order_line.create({
                    'order_id': self.id,
                    'name': loyalty_id.disc_product_id.name,
                    'product_uom_qty': 1,
                    'product_uom': loyalty_id.disc_product_id.uom_id.id,
                    'product_id': loyalty_id.disc_product_id.id,
                    'price_unit': -1 * round(self.redeemed_value),
                    'tax_id': False,
                    'ordered_qty':1


                })

                if redeem_line:

                    balance_loyalty_points = self.partner_id.loyalty_points - self.redeemed_coins

                    self.partner_id.loyalty_points = balance_loyalty_points














