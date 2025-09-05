{
    "name": "GPT-5 Assistant (Final Groq)",
    "version": "18.0.2.0.0",
    "summary": "Plain-HTML AI assistant with Groq defaults, no double-confirm, and Dangerous/Sudo Mode awareness.",
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
