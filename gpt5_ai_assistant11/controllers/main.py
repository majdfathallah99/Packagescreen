from odoo import http
from odoo.http import request

class AiAssistantProbe(http.Controller):
    @http.route("/ai_assistant/ping", type="http", auth="public")
    def ping(self, **kw):
        return "OK"

    @http.route("/ai_assistant/app", type="http", auth="user")
    def app_page(self, **kw):
        return request.render("gpt5_ai_assistant.page_min", {})
