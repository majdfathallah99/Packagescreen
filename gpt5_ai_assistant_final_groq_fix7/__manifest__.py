{
    "name": "GPT-5 Assistant (Final Groq Fix7)",
    "version": "18.0.2.0.7",
    "summary": "Groq defaults, diagnostics, safe clear, single-confirm, and guaranteed non-empty replies.",
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
