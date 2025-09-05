{
    'name': 'GPT-5 Assistant (Final Groq F23)',
    'version': '18.0.3.0.2',
    'summary': 'Adds safe env escalation (_env) for instances without env.sudo(); keeps diagnostics, shortcuts, product count tool.',
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
