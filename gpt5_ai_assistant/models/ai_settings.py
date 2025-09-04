from odoo import api, fields, models

class AiAssistantSettings(models.TransientModel):
    _name = "ai.assistant.settings"
    _inherit = "res.config.settings"
    _description = "GPT-5 Assistant Settings"

    ai_api_key = fields.Char(string="API Key")
    ai_model = fields.Char(string="Model", default="gpt-4o-mini")
    ai_base_url = fields.Char(string="Base URL")
    ai_system_prompt = fields.Text(string="System Prompt", default="You are a helpful AI assistant inside Odoo.")

    def set_values(self):
        super().set_values()
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("ai_assistant.api_key", self.ai_api_key or "")
        icp.set_param("ai_assistant.model", self.ai_model or "gpt-4o-mini")
        icp.set_param("ai_assistant.base_url", self.ai_base_url or "")
        icp.set_param("ai_assistant.system_prompt", self.ai_system_prompt or "")

    @api.model
    def get_values(self):
        res = super().get_values()
        icp = self.env["ir.config_parameter"].sudo()
        res.update(
            ai_api_key=icp.get_param("ai_assistant.api_key", default=""),
            ai_model=icp.get_param("ai_assistant.model", default="gpt-4o-mini"),
            ai_base_url=icp.get_param("ai_assistant.base_url", default=""),
            ai_system_prompt=icp.get_param("ai_assistant.system_prompt", default="You are a helpful AI assistant inside Odoo."),
        )
        return res
