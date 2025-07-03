from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BlogCategory(models.Model):
    _name = 'blog.category'
    _description = 'Blog Categories'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
        help='Name of the blog category'
    )
    description = fields.Text(
        string='Description',
        help='Category description'
    )
    color = fields.Integer(
        string='Color',
        help='Color for category display'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of display'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to hide the category'
    )

    # Related fields
    article_count = fields.Integer(
        string='Articles Count',
        compute='_compute_article_count',
        store=True
    )
    article_ids = fields.Many2many(
        'blog.articles',
        'article_category_rel',
        'category_id',
        'article_id',
        string='Articles'
    )

    @api.depends('article_ids')
    def _compute_article_count(self):
        for category in self:
            category.article_count = len(category.article_ids)

    @api.constrains('name')
    def _check_name_unique(self):
        for record in self:
            if record.name:
                domain = [('name', '=ilike', record.name),
                          ('id', '!=', record.id)]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        f"Category '{record.name}' already exists.")

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.article_count})"
            result.append((record.id, name))
        return result
