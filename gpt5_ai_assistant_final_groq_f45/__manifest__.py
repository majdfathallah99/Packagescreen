{
    'name': 'GPT-5 Assistant (Final Groq F30)',
    'version': '18.0.3.post2',
    'summary': 'Shows full chat history with scroll, adds transcript export; keeps Groq defaults and tools.',
    'category': 'Tools',
    'depends': ['base', 'sale_management', 'purchase', 'product'],
    'data': [
        'data/menu.xml',
        'security/ir.model.access.csv'
    , 'data/menu_live.xml', 'views/menu_live.xml'],
    'external_dependencies': {
        'python': ['openai>=1.40.0']
    },
    'assets': {},
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
,
    'images': ['static/description/icon.png'],
}