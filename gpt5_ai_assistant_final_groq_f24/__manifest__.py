{
    'name': 'GPT-5 Assistant (Final Groq F24)',
    'version': '18.0.3.0.3',
    'summary': 'Shows full chat history with scroll, adds transcript export; keeps Groq defaults and tools.',
    'category': 'Tools',
    'depends': ['base', 'sale_management', 'purchase', 'product'],
    'data': [
        'data/menu.xml',
        'security/ir.model.access.csv'
    ],
    'external_dependencies': {
        'python': ['openai>=1.40.0']
    },
    'assets': {},
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
