from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class BlogTag(models.Model):
    _name = 'blog.tag'
    _description = 'Blog Tags'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Tag Name',
        required=True,
        help='Name of the blog tag'
    )
    color = fields.Integer(
        string='Color',
        help='Color for tag display'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to hide the tag'
    )

    # Related fields
    article_count = fields.Integer(
        string='Articles Count',
        compute='_compute_article_count',
        store=True
    )
    article_ids = fields.Many2many(
        'blog.articles',
        'article_tag_rel',
        'tag_id',
        'article_id',
        string='Articles'
    )

    @api.depends('article_ids')
    def _compute_article_count(self):
        for tag in self:
            tag.article_count = len(tag.article_ids)

    @api.constrains('name')
    def _check_name_format(self):
        for record in self:
            if record.name:
                # Tag names should be lowercase and no spaces
                if not re.match(r'^[a-z0-9-]+$', record.name.lower()):
                    raise ValidationError(
                        "Tag names should contain only lowercase letters, numbers, and hyphens.")

    @api.constrains('name')
    def _check_name_unique(self):
        for record in self:
            if record.name:
                domain = [('name', '=ilike', record.name),
                          ('id', '!=', record.id)]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        f"Tag '{record.name}' already exists.")

    @api.model
    def create(self, vals):
        # Auto-format tag name
        if 'name' in vals:
            vals['name'] = vals['name'].lower().replace(' ', '-')
        return super().create(vals)

    def write(self, vals):
        # Auto-format tag name
        if 'name' in vals:
            vals['name'] = vals['name'].lower().replace(' ', '-')
        return super().write(vals)

    def name_get(self):
        result = []
        for record in self:
            name = f"#{record.name} ({record.article_count})"
            result.append((record.id, name))
        return result
