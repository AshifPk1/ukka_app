# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class LoyaltyProgram(models.Model):
    _name = 'sale.loyalty.program'
    _description = 'Loyalty Program'

    name = fields.Char(string='Loyalty Program Name', index=True, required=True, help="An internal identification for the loyalty program configuration")
    pp_currency = fields.Float(string='Points per currency', help="How many loyalty points are given to the customer by sold currency")
    pp_product = fields.Float(string='Points per product', help="How many loyalty points are given to the customer by product sold")
    pp_order = fields.Float(string='Points per order', help="How many loyalty points are given to the customer for each sale or order")
    rounding = fields.Float(string='Points Rounding', default=1, help="The loyalty point amounts are rounded to multiples of this value.")
    rule_ids = fields.One2many('sale.loyalty.rule', 'loyalty_program_id', string='Rules')
    reward_ids = fields.One2many('sale.loyalty.reward', 'loyalty_program_id', string='Rewards')
    redeem_type = fields.Selection([('discount', 'Discount (in value)')], required=True, help='The type of the reward',string="Redeem Type")
    minimum_points = fields.Float(help='The minimum amount of points the customer must have to qualify for this redeem')
    disc_product_id = fields.Many2one('product.product', string='Discount Product', help='The product that represents the price to be redeemed')
    point_amount = fields.Float(string="1 point")
    # min_percent_of_total = fields.Float(string="Min Total(%)")





class LoyaltyRule(models.Model):
    _name = 'sale.loyalty.rule'
    _description = 'Loyalty Rule'

    name = fields.Char(index=True, required=True, help="An internal identification for this loyalty program rule")
    loyalty_program_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program', help='The Loyalty Program this exception belongs to')
    rule_type = fields.Selection([('product', 'Product')], old_name='type', required=True, default='product', help='Does this rule affects products, or a category of products ?')
    product_id = fields.Many2one('product.product', string='Target Product', help='The product affected by the rule')
    category_id = fields.Many2one('product.category', string='Target Category', help='The category affected by the rule')
    cumulative = fields.Boolean(help='The points won from this rule will be won in addition to other rules')
    pp_product = fields.Float(string='Points per product', help='How many points the product will earn per product ordered')
    pp_currency = fields.Float(string='Points per currency', help='How many points the product will earn per value sold')

class LoyaltyReward(models.Model):
    _name = 'sale.loyalty.reward'
    _description = 'Loyalty Reward'


    name = fields.Char(index=True, required=True, help='An internal identification for this loyalty reward')
    loyalty_program_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program', help='The Loyalty Program this reward belongs to')
    minimum_points = fields.Float(help='The minimum amount of points the customer must have to qualify for this reward')
    reward_type = fields.Selection([('resale', 'Discount (in value)')], old_name='type', required=True, help='The type of the reward')
    # gift_product_id = fields.Many2one('product.product', string='Gift Product', help='The product given as a reward')
    point_cost = fields.Float(string='Reward Cost', help="If the reward is a gift, that's the cost of the gift in points. If the reward type is a discount that's the cost in point per currency (e.g. 1 point per $)")
    # discount_product_id = fields.Many2one('product.product', string='Discount Product', help='The product used to apply discounts')
    # discount = fields.Float(help='The discount percentage')
    point_product_id = fields.Many2one('product.product', string='Point Product', help='The product that represents a point that is sold by the customer')

