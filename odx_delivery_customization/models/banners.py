from odoo import fields, models, api, _


class BannerImages(models.Model):
    _name = 'banner.images'
    _description = 'Select banners for main display in app'

    description = fields.Char(string="Description")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    banner_image = fields.Binary(string="Image")
    name = fields.Char(string="Name")
    is_active = fields.Boolean(string="Active")
    category_id = fields.Many2one('product.category',string="Category")
