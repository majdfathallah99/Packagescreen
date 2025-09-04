{
    "name": "GPT-5 Assistant (Groq Default)",
    "version": "18.0.1.0.4",
    "summary": "Plain-HTML AI assistant with Groq defaults (OpenAI-compatible).",
    "category": "Tools",
    "depends": ["base", "sale_management", "purchase", "product"],
    "data": [
        "data/menu.xml",
        "data/config_params.xml",
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
