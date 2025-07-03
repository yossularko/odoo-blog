from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class BlogComment(models.Model):
    _name = 'blog.comment'
    _description = 'Blog Comments'
    _order = 'create_date desc'
    _rec_name = 'content_preview'

    # Basic fields
    content = fields.Html(
        string='Comment',
        required=True,
        help='Comment content'
    )
    article_id = fields.Many2one(
        'blog.articles',
        string='Article',
        required=True,
        ondelete='cascade',
        help='Article being commented on'
    )
    author_id = fields.Many2one(
        'res.users',
        string='Author',
        required=True,
        default=lambda self: self.env.user,
        help='Comment author'
    )

    # Optional fields for public comments
    author_name = fields.Char(
        string='Author Name',
        help='Name for public/guest comments'
    )
    author_email = fields.Char(
        string='Author Email',
        help='Email for public/guest comments'
    )

    # Status fields
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to hide comment'
    )
    is_approved = fields.Boolean(
        string='Approved',
        default=True,
        help='Comment approval status'
    )
    is_public = fields.Boolean(
        string='Public Comment',
        default=False,
        help='Comment from non-logged user'
    )

    # Hierarchical comments (replies)
    parent_id = fields.Many2one(
        'blog.comment',
        string='Parent Comment',
        help='Parent comment for replies'
    )
    child_ids = fields.One2many(
        'blog.comment',
        'parent_id',
        string='Replies'
    )

    # Computed fields
    content_preview = fields.Char(
        string='Preview',
        compute='_compute_content_preview',
        store=True
    )
    reply_count = fields.Integer(
        string='Replies',
        compute='_compute_reply_count',
        store=True
    )
    author_display = fields.Char(
        string='Author',
        compute='_compute_author_display',
        store=True
    )
    comment_level = fields.Integer(
        string='Level',
        compute='_compute_comment_level',
        store=True,
        help='Nesting level of comment'
    )

    @api.depends('content')
    def _compute_content_preview(self):
        for comment in self:
            if comment.content:
                # Remove HTML tags and get first 100 characters
                import re
                clean_content = re.sub(r'<[^>]+>', '', comment.content or '')
                comment.content_preview = clean_content[:100] + (
                    '...' if len(clean_content) > 100 else '')
            else:
                comment.content_preview = 'Empty comment'

    @api.depends('child_ids')
    def _compute_reply_count(self):
        for comment in self:
            comment.reply_count = len(comment.child_ids)

    @api.depends('author_id', 'author_name', 'is_public')
    def _compute_author_display(self):
        for comment in self:
            if comment.is_public and comment.author_name:
                comment.author_display = f"{comment.author_name} (Guest)"
            elif comment.author_id:
                comment.author_display = comment.author_id.name
            else:
                comment.author_display = "Anonymous"

    @api.depends('parent_id')
    def _compute_comment_level(self):
        for comment in self:
            level = 0
            parent = comment.parent_id
            while parent and level < 10:  # Prevent infinite loop
                level += 1
                parent = parent.parent_id
            comment.comment_level = level

    @api.constrains('content')
    def _check_content_length(self):
        for comment in self:
            if comment.content:
                clean_content = re.sub(r'<[^>]+>', '', comment.content)
                if len(clean_content.strip()) < 5:
                    raise ValidationError(
                        "Comment must be at least 5 characters long.")

    @api.constrains('parent_id')
    def _check_comment_hierarchy(self):
        for comment in self:
            if comment.parent_id:
                # Check if parent belongs to same article
                if comment.parent_id.article_id != comment.article_id:
                    raise ValidationError(
                        "Reply must be on the same article as parent comment.")

                # Prevent deep nesting (max 3 levels)
                if comment.comment_level > 3:
                    raise ValidationError(
                        "Maximum comment nesting level is 3.")

    @api.constrains('author_email')
    def _check_email_format(self):
        for comment in self:
            if comment.author_email and comment.is_public:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, comment.author_email):
                    raise ValidationError(
                        "Please enter a valid email address.")

    def name_get(self):
        result = []
        for comment in self:
            name = f"{comment.author_display}: {comment.content_preview}"
            result.append((comment.id, name))
        return result

    def action_approve(self):
        """Approve comment"""
        self.write({'is_approved': True, 'active': True})

    def action_reject(self):
        """Reject/hide comment"""
        self.write({'is_approved': False, 'active': False})

    def action_reply(self):
        """Open reply form"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reply to Comment',
            'res_model': 'blog.comment',
            'view_mode': 'form',
            'context': {
                'default_article_id': self.article_id.id,
                'default_parent_id': self.id,
                'default_author_id': self.env.user.id,
            },
            'target': 'new',
        }
