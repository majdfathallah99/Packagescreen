{
  "name": "GPT-5 Assistant (Final Groq F21)",
  "version": "18.0.3.0.0",
  "summary": "Groq defaults, diagnostics, safe clear, non-empty replies, product count tool, and server shortcuts.",
  "category": "Tools",
  "depends": [
    "base",
    "sale_management",
    "purchase",
    "product"
  ],
  "data": [
    "data/menu.xml",
    "security/ir.model.access.csv"
  ],
  "external_dependencies": {
    "python": [
      "openai>=1.40.0"
    ]
  },
  "assets": {},
  "installable": true,
  "application": true,
  "license": "LGPL-3"
}