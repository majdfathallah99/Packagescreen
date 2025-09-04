# -*- coding: utf-8 -*-
{
    "name": "GPT-5 AI Assistant",
    "summary": "Self-contained chat assistant page (safe assets) for Odoo 17/18",
    "version": "18.0.2.0.0",
    "category": "Productivity",
    "author": "You + ChatGPT",
    "website": "https://example.com",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/ai_settings_view.xml",
        "views/page_templates.xml"
    ],
    "assets": {
        "gpt5_ai_assistant.assets": [
            "gpt5_ai_assistant/static/src/js/chat_page.js",
            "gpt5_ai_assistant/static/src/xml/void.xml"
        ]
    },
    "installable": True,
    "application": True
}
