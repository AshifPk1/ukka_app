from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Product(models.Model):
    _inherit = 'product.product'
    _order = 'sequence,id'

    own_product = fields.Boolean(string="Own Product")
    malayalam_name = fields.Char(string="In Malayalam")
    product_images_ids = fields.One2many('product.images','product_id', string='Attach Product Images')
    product_uom_ids = fields.One2many('product.uom.setting', 'product_uom_id', string='Set Product UoM')
    mrp = fields.Float(string="MRP")
    product_tag_ids = fields.Many2many('product.tags', string='Tags')
    is_offer = fields.Boolean(string="Has Offer")
    display_uom = fields.Many2one('product.uom.setting', string="Display UoM", compute='_name_compute')
    is_featured = fields.Boolean(string="Is Featured")
    show_in_app = fields.Boolean(string='Available in app')
    sequence = fields.Integer(string='Sequence', default=10)

    @api.depends('product_uom_ids', 'uom_id')
    def _name_compute(self):
        for record in self:
            if record.product_uom_ids:
                record.display_uom = record.product_uom_ids[0].id
                # uom_setting = record.product_uom_ids.filtered(lambda line: line.uom_id.id == record.uom_id.id)
                # if uom_setting:
                #     record.display_uom = uom_setting[0].id
                # else:
                #     record.display_uom = record.product_uom_ids[0].id
            else:

                # raise UserError(_('Please select Uom'))
                uom_setting = record.product_uom_ids.filtered(lambda line: line.uom_id.id == record.uom_id.id)
                if not uom_setting:
                    product_uom = self.env['product.uom.setting'].create({
                        'name':'1' + ' ' + record.uom_id.name,
                        'quantity': '1',
                        'uom_id':record.uom_id.id,
                        'product_uom_id':record.id
                    })
                    record.display_uom = product_uom.id
                # check_uom = record.product_uom_ids.filtered(lambda line: line.uom_id.category_id.id == record.uom_id.category_id.id)
                # if check_uom:
                #     for rec in check_uom:
                #         rec = False
                # for product_uom_id in record.product_uom_ids:
                #     print("truee")
                #     if record.uom_id.category_id.id != product_uom_id.uom_id.category_id.id:
                #      print("herrr")
                #      product_uom_id.unlink()


                # if record.product_uom_ids:
                #     if not record.product_uom_ids.filtered(lambda line: line.uom_id.id == record.uom_id.id):
                #         product_uom = self.env['product.uom.setting'].create({
                #             'name': '1' + ' ' + record.uom_id.name,
                #             'quantity': '1',
                #             'uom_id': record.uom_id.id,
                #             'product_uom_id': record.id
    @api.model_create_multi            #         })
    def create(self, vals_list):
        products = super(Product, self.with_context(create_product_product=True)).create(vals_list)
        check_uom = self.product_uom_ids.filtered(
            lambda line: line.uom_id.category_id.id != self.uom_id.category_id.id)

        if check_uom:
            for rec in check_uom:
                rec.unlink()

        return products


    def write(self, values):


        res = super(Product, self).write(values)
        check_uom = self.product_uom_ids.filtered(
            lambda line: line.uom_id.category_id.id != self.uom_id.category_id.id)

        if check_uom:
            for rec in check_uom:
                rec.unlink()

        return res






class ProductCategry(models.Model):
    _name = 'product.category'
    _inherit = ['product.category', 'mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'sequence,id'

    image = fields.Binary("Image")
    image_1920 = fields.Image("Variant Image", max_width=1920, max_height=1920)

    is_restuarant_category = fields.Boolean("Is Restuarant")
    is_miscellaneous_category = fields.Boolean("Is Miscellaneous")
    is_delivery = fields.Boolean("Is Delivery")
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    image_512 = fields.Image("Image 512", related="image_1920", max_width=512, max_height=512, store=True)
    image_256 = fields.Image("Image 256", related="image_1920", max_width=256, max_height=256, store=True)
    image_128 = fields.Image("Image 128", related="image_1920", max_width=128, max_height=128, store=True)

    def _compute_image_512(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_512 = record.image

    def _compute_image_256(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_256 = record.image_variant_256 or record.product_tmpl_id.image_256

    def _compute_image_128(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_128 = record.image_variant_128 or record.product_tmpl_id.image_128

class ProductImages(models.Model):
    _name = 'product.images'
    _description = "To attach multiple images for the products"

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    product_id = fields.Many2one(comodel_name="product.product",string="Product")
    image_000 = fields.Binary(string="Image")

class ProductUomSetting(models.Model):
    _name = 'product.uom.setting'
    _description = "To display the product uom per quantity"
    _order = 'sequence,id'


    name = fields.Char(string="Name",compute='_name_compute')
    quantity = fields.Float(string="Quantity")
    product_uom_id = fields.Many2one(comodel_name="product.product", string="Product")
    uom_id = fields.Many2one(comodel_name="uom.uom",string="Unit of Measure")
    sequence = fields.Integer(string='Sequence', default=10)
    price = fields.Float('Price', compute='_compute_price')
    strike_price = fields.Float('MRP',compute='_compute_strike_price')


    def _compute_price(self):
        for rec in self:
            rec.price = 0
            if rec.product_uom_id and rec.product_uom_id.uom_id:
                price_rate = rec.product_uom_id.uom_id._compute_price(rec.product_uom_id.lst_price, rec.uom_id)
                line_price = price_rate * rec.quantity
                rec.price = round(line_price, 2)

    def _compute_strike_price(self):
        for rec in self:
            rec.strike_price = 0
            if rec.product_uom_id and rec.product_uom_id.uom_id:
                price_rate = rec.product_uom_id.uom_id._compute_price(rec.product_uom_id.mrp, rec.uom_id)
                line_strike_price =  price_rate * rec.quantity
                rec.strike_price = round(line_strike_price,2)





    # def name_get(self):
    #     result = []
    #     for record in self:

    #         if record.product_uom_ids:
    #             name = str(record.quantity) + ' ' + record.uom_id.name
    #             result.append((record.id, name))
    #
    #     return result

    def _name_compute(self):
        for record in self:
            if record.uom_id:
                record.name = str(record.quantity) + ' ' + record.uom_id.name + ','+ str(record.price) + ','+str(record.uom_id.id) + ',' + str(record.strike_price)
            # else:
            #     record.name = '1' + ' ' + record.product_id.uom_id.name





class ProductTags(models.Model):
    _name = 'product.tags'
    _description = "To allow the user search based on the names in product tags"

    name = fields.Char(string="Name")