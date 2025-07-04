from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
import logging

_logger = logging.getLogger(__name__)


class BlogArticles(models.Model):
    _name = 'blog.articles'
    _description = 'Blog Articles'
    _order = 'create_date desc'
    _rec_name = 'title'

    # Basic Fields
    slug = fields.Char(
        string='Slug',
        required=False,
        help='URL-friendly version of the title (auto-generated if empty)'
    )
    title = fields.Char(
        string='Title',
        required=True,
        help='Article title'
    )
    body = fields.Html(
        string='Content',
        required=True,
        help='Article content'
    )
    cover_image = fields.Binary(
        string='Cover Image',
        help='Cover image for the article'
    )
    author = fields.Many2one(
        'res.users',
        string='Author',
        required=True,
        default=lambda self: self.env.user,
        help='Article author'
    )

    # Additional Fields
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to hide the article without deleting it'
    )
    published_date = fields.Datetime(
        string='Published Date',
        default=fields.Datetime.now,
        help='Date when the article was published'
    )

    # Computed Fields
    word_count = fields.Integer(
        string='Word Count',
        compute='_compute_word_count',
        store=True,
        help='Number of words in the article body'
    )

    # Categories & Tags
    category_ids = fields.Many2many(
        'blog.category',
        'article_category_rel',
        'article_id',
        'category_id',
        string='Categories',
        help='Categories for this article'
    )
    tag_ids = fields.Many2many(
        'blog.tag',
        'article_tag_rel',
        'article_id',
        'tag_id',
        string='Tags',
        help='Tags for this article'
    )

    # Computed fields for display
    category_names = fields.Char(
        string='Categories',
        compute='_compute_category_names',
        store=True
    )
    tag_names = fields.Char(
        string='Tags',
        compute='_compute_tag_names',
        store=True
    )

    # Comments
    comment_ids = fields.One2many(
        'blog.comment',
        'article_id',
        string='Comments'
    )
    comment_count = fields.Integer(
        string='Comments',
        compute='_compute_comment_count',
        store=True
    )
    approved_comment_count = fields.Integer(
        string='Approved Comments',
        compute='_compute_comment_count',
        store=True
    )
    last_comment_date = fields.Datetime(
        string='Last Comment',
        compute='_compute_last_comment_date',
        store=True
    )
    
    # Comment settings
    allow_comments = fields.Boolean(
        string='Allow Comments',
        default=True,
        help='Allow users to comment on this article'
    )
    moderate_comments = fields.Boolean(
        string='Moderate Comments',
        default=False,
        help='Require approval for new comments'
    )

    @api.depends('category_ids')
    def _compute_category_names(self):
        for record in self:
            if record.category_ids:
                record.category_names = ', '.join(record.category_ids.mapped('name'))
            else:
                record.category_names = ''
    
    @api.depends('tag_ids')
    def _compute_tag_names(self):
        for record in self:
            if record.tag_ids:
                record.tag_names = ', '.join([f"#{tag}" for tag in record.tag_ids.mapped('name')])
            else:
                record.tag_names = ''

    @api.depends('comment_ids', 'comment_ids.is_approved', 'comment_ids.active')
    def _compute_comment_count(self):
        for article in self:
            all_comments = article.comment_ids.filtered(lambda c: c.active)
            approved_comments = all_comments.filtered(lambda c: c.is_approved)
            
            article.comment_count = len(all_comments)
            article.approved_comment_count = len(approved_comments)
    
    @api.depends('comment_ids.create_date')
    def _compute_last_comment_date(self):
        for article in self:
            if article.comment_ids:
                article.last_comment_date = max(article.comment_ids.mapped('create_date'))
            else:
                article.last_comment_date = False

    @api.depends('body')
    def _compute_word_count(self):
        """Compute word count from body content"""
        for record in self:
            if record.body:
                # Remove HTML tags and count words
                import html
                text = html.unescape(record.body)
                text = re.sub(r'<[^>]+>', '', text)
                words = text.split()
                record.word_count = len(words)
            else:
                record.word_count = 0

    @api.model
    def create(self, vals):
        """Override create to auto-generate slug"""
        # Auto-generate slug from title if not provided or empty
        if 'title' in vals and (not vals.get('slug') or not vals.get('slug').strip()):
            vals['slug'] = self._generate_unique_slug(vals['title'])

        # Ensure author is set to current user if not provided
        if not vals.get('author'):
            vals['author'] = self.env.user.id

        _logger.info(
            f"Creating blog article with title: {vals.get('title')} and slug: {vals.get('slug')}")
        return super(BlogArticles, self).create(vals)

    def write(self, vals):
        """Override write to handle slug updates"""
        # Update slug if title is changed and current slug is empty
        if 'title' in vals:
            for record in self:
                if not record.slug or not record.slug.strip():
                    vals['slug'] = record._generate_unique_slug(
                        vals.get('title', record.title))
                    _logger.info(
                        f"Auto-generated slug: {vals.get('slug')} for article: {record.title}")
                    break
        return super(BlogArticles, self).write(vals)
    
    def copy(self, default=None):
        """Override copy to handle categories, tags, and comments"""
        if default is None:
            default = {}
        
        # Generate unique identifier once
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # Handle slug uniqueness
        if 'slug' not in default:
            base_slug = self.slug or 'article'
            default['slug'] = f"{base_slug}-copy-{unique_id}"
        
        # Handle title uniqueness  
        if 'title' not in default:
            default['title'] = f"{self.title} (Copy {unique_id})"
        
        # Copy categories and tags
        if 'category_ids' not in default:
            default['category_ids'] = [(6, 0, self.category_ids.ids)]
        
        if 'tag_ids' not in default:
            default['tag_ids'] = [(6, 0, self.tag_ids.ids)]
        
        # DON'T copy comments (comments are specific to original article)
        if 'comment_ids' not in default:
            default['comment_ids'] = []
        
        # Copy comment settings
        if 'allow_comments' not in default:
            default['allow_comments'] = self.allow_comments
        
        if 'moderate_comments' not in default:
            default['moderate_comments'] = self.moderate_comments
        
        # Ensure author is set
        if 'author' not in default:
            default['author'] = self.env.user.id
        
        # Update published date for copies
        if 'published_date' not in default:
            default['published_date'] = fields.Datetime.now()
        
        return super(BlogArticles, self).copy(default)
    
    def action_view_comments(self):
        """Open comments view for this article"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Comments for: {self.title}',
            'res_model': 'blog.comment',
            'view_mode': 'tree,form',
            'domain': [('article_id', '=', self.id)],
            'context': {
                'default_article_id': self.id,
                'search_default_article_comments': 1,
            },
        }
    
    def action_add_comment(self):
        """Add new comment to this article"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Comment',
            'res_model': 'blog.comment',
            'view_mode': 'form',
            'context': {
                'default_article_id': self.id,
                'default_author_id': self.env.user.id,
            },
            'target': 'new',
        }

    def _generate_slug(self, title):
        """Generate URL-friendly slug from title"""
        if not title or not title.strip():
            return 'article'

        # Convert to lowercase and clean up
        slug = title.strip().lower()

        # Remove special characters except letters, numbers, spaces, and hyphens
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)

        # Replace spaces with hyphens
        slug = re.sub(r'\s+', '-', slug)

        # Replace multiple hyphens with single hyphen
        slug = re.sub(r'-+', '-', slug)

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        # If slug becomes empty after cleaning, use default
        if not slug:
            slug = 'article'

        return slug

    def _generate_unique_slug(self, title):
        """Generate unique URL-friendly slug from title"""
        base_slug = self._generate_slug(title)

        if not base_slug:
            base_slug = 'article'

        # Check if slug already exists
        counter = 1
        unique_slug = base_slug

        # Keep incrementing counter until we find a unique slug
        while self.search_count([('slug', '=', unique_slug), ('id', '!=', self.id or 0)]) > 0:
            unique_slug = f"{base_slug}-{counter}"
            counter += 1

        return unique_slug

    @api.constrains('slug')
    def _check_slug_unique(self):
        """Ensure slug is unique across all articles"""
        for record in self:
            if record.slug and record.slug.strip():
                domain = [('slug', '=', record.slug), ('id', '!=', record.id)]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        f"Slug must be unique. '{record.slug}' is already used by another article.")

    @api.constrains('slug')
    def _check_slug_format(self):
        """Validate slug format - only lowercase letters, numbers, and hyphens"""
        for record in self:
            if record.slug and record.slug.strip():
                if not re.match(r'^[a-z0-9-]+$', record.slug):
                    raise ValidationError(
                        "Slug can only contain lowercase letters, numbers, and hyphens.")

                # Additional validation: slug cannot start or end with hyphen
                if record.slug.startswith('-') or record.slug.endswith('-'):
                    raise ValidationError(
                        "Slug cannot start or end with a hyphen.")

                # Additional validation: slug cannot have consecutive hyphens
                if '--' in record.slug:
                    raise ValidationError(
                        "Slug cannot contain consecutive hyphens.")

    @api.constrains('title')
    def _check_title_length(self):
        """Validate title length"""
        for record in self:
            if record.title and len(record.title) > 200:
                raise ValidationError(
                    "Title cannot be longer than 200 characters.")

    def name_get(self):
        """Custom name_get to display title and author"""
        result = []
        for record in self:
            name = f"{record.title} (by {record.author.name})"
            result.append((record.id, name))
        return result

    def toggle_active(self):
        """Toggle active state of the article"""
        for record in self:
            record.active = not record.active

    def duplicate_article(self):
        """Duplicate article with new slug"""
        self.ensure_one()

        # Create new title and slug for duplicate
        new_title = f"{self.title} (Copy)"
        new_slug = self._generate_unique_slug(new_title)

        # Copy the record
        new_article = self.copy({
            'title': new_title,
            'slug': new_slug,
            'published_date': fields.Datetime.now(),
        })

        # Return action to open the new article
        return {
            'type': 'ir.actions.act_window',
            'name': 'Blog Article',
            'res_model': 'blog.articles',
            'res_id': new_article.id,
            'view_mode': 'form',
            'target': 'current',
        }
