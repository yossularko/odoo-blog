{
    'name': 'My Blog',
    'version': '17.0.3.0.0',
    'category': 'Website/Website',
    'summary': 'Blog Management System with Categories & Tags',
    'description': """
        Enhanced Blog addon for managing articles with:
        - Articles with slug, title, body, cover image, author
        - Categories for organizing articles by topics
        - Tags for labeling and keyword filtering
        - Comment system with hierarchical replies
        - Comment moderation and approval workflow
        - Public and registered user comments
        - Auto-generate unique slug from title
        - Complete validation and error handling
        - Rich kanban views with visual organization
    """,
    'author': 'Yos Sularko',
    'website': 'https://www.yourwebsite.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/articles_views.xml',
        'views/category_views.xml',
        'views/tag_views.xml',
        'views/comment_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'data/demo_categories.xml',
        'data/demo_tags.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}