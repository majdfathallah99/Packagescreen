{
    "name": "GPT-5 Assistant (Final Groq Fix5)",
    "version": "18.0.2.0.5",
    "summary": "Groq defaults, solid redirects, single-confirm, and a diagnostics page.",
    "category": "Tools",
    "depends": ["base", "sale_management", "purchase", "product"],
    "data": [
        "data/menu.xml",
        "security/ir.model.access.csv"
    ],
    "external_dependencies": {
        "python": ["openai>=1.40.0"]
    },
    "assets": {},
    "installable": True,
    "application": True,
    "license": "LGPL-3"
}
