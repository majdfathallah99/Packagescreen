# -*- coding: utf-8 -*-
import html as _html
import json
from datetime import datetime, timedelta
from odoo import http, tools
from odoo.http import request

SYSTEM_PROMPT = """You are an Odoo AI assistant. You can read the user's intent and, when helpful,
call tools to perform actions inside Odoo (create products/customers, create sale orders, simple reports).
Always return a concise, helpful answer.
If a requested action changes data (sell/buy/create), ask for confirmation first unless the configuration
'AI Assistant: Dangerous/Sudo Mode' is explicitly enabled.
Prefer Arabic if the user writes Arabic; otherwise use English.
Keep replies short and to the point unless the user asks for details.
When showing money, include the currency from Odoo if available.
"""

def _get_conf(key, default=False):
    return request.env['ir.config_parameter'].sudo().get_param(key, default)

def _set_conf(key, value):
    request.env['ir.config_parameter'].sudo().set_param(key, value)

def _normalize_base_url(url):
    if not url:
        return None
    u = (url or "").strip()
    if not u:
        return None
    while u.endswith("/"):
        u = u[:-1]
    low = u.lower()
    if "groq" in low and "/openai" not in low:
        return "https://api.groq.com/openai/v1"
    if "openrouter.ai" in low and "/api/" not in low:
        return "https://openrouter.ai/api/v1"
    if not low.endswith("/v1"):
        return u + "/v1"
    return u

def _client():
    try:
        from openai import OpenAI
    except Exception:
        raise Exception("OpenAI SDK missing. Install with: pip install openai")
    api_key = _get_conf("ai_assistant.openai_api_key") or tools.config.get("openai_api_key")
    if not api_key:
        raise Exception("API key is not configured. Go to /ai_assistant/settings.")
    base_url_raw = _get_conf("ai_assistant.openai_base_url") or None
    base_url = _normalize_base_url(base_url_raw)
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)

def _danger_mode():
    v = (_get_conf("ai_assistant.danger_mode") or "false").lower()
    return v in ("1","true","yes","on")

def _model_name():
    return (_get_conf("ai_assistant.model") or "llama-3.1-70b-versatile").strip()

def _currency_symbol():
    company = request.env.company
    return company.currency_id.symbol if company and company.currency_id else "$"

def _ensure_messages():
    if 'ai_messages' not in request.session:
        request.session['ai_messages'] = []
    return request.session['ai_messages']

# ---- Tool implementations ----

def tool_create_product(name:str, list_price:float=0.0, uom_name:str="Units", default_code:str=None):
    env = request.env.sudo() if _danger_mode() else request.env
    Product = env['product.product']
    Uom = env['uom.uom']
    uom = Uom.search([('name','ilike', uom_name)], limit=1)
    vals = {'name': name, 'list_price': list_price or 0.0}
    if uom:
        vals['uom_id'] = uom.id
        vals['uom_po_id'] = uom.id
    if default_code:
        vals['default_code'] = default_code
    p = Product.create(vals)
    return {"id": p.id, "name": p.display_name, "price": p.list_price, "uom": uom.name if uom else None}

def tool_create_partner(name:str, phone:str=None, email:str=None, customer:bool=True, supplier:bool=False):
    env = request.env.sudo() if _danger_mode() else request.env
    Partner = env['res.partner']
    p = Partner.create({
        'name': name,
        'phone': phone or False,
        'email': email or False,
        'customer_rank': 1 if customer else 0,
        'supplier_rank': 1 if supplier else 0,
    })
    return {"id": p.id, "name": p.display_name, "phone": p.phone, "email": p.email}

def _find_partner_by_name(name):
    env = request.env.sudo() if _danger_mode() else request.env
    Partner = env['res.partner']
    partner = Partner.search([('name','ilike', name)], limit=1)
    if not partner:
        raise Exception(f"Partner '{name}' not found.")
    return partner

def _find_product_by_name(name):
    env = request.env.sudo() if _danger_mode() else request.env
    Product = env['product.product']
    product = Product.search([('name','ilike', name)], limit=1)
    if not product:
        raise Exception(f"Product '{name}' not found.")
    return product

def tool_create_sale_order(partner_name:str, lines:list):
    env = request.env.sudo() if _danger_mode() else request.env
    Sale = env['sale.order']
    partner = _find_partner_by_name(partner_name)
    order_lines = []
    for ln in (lines or []):
        prod = _find_product_by_name(ln.get('product_name'))
        qty = float(ln.get('qty') or 1.0)
        price = ln.get('price')
        line_vals = {'product_id': prod.id, 'product_uom_qty': qty}
        if price is not None:
            line_vals['price_unit'] = float(price)
        order_lines.append((0,0,line_vals))
    so = Sale.create({'partner_id': partner.id, 'order_line': order_lines})
    return {"id": so.id, "name": so.name, "customer": partner.display_name, "total": so.amount_total}

def tool_sales_summary(period:str="today"):
    env = request.env
    now = fields_now()
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period in ("this_week", "week"):
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    domain = [('date_order','>=', start)]
    orders = env['sale.order'].search(domain, order='date_order desc', limit=50)
    total = sum(o.amount_total for o in orders)
    count = len(orders)
    lines = [{"name": o.name, "customer": o.partner_id.display_name, "total": o.amount_total} for o in orders]
    return {"period": period, "count": count, "total": total, "currency": _currency_symbol(), "recent": lines}

def fields_now():
    try:
        return request.env['ir.fields.converter'].context_timestamp(request.env.user, datetime.utcnow())
    except Exception:
        return datetime.utcnow()

TOOLS_SPEC = [
    {"type":"function","function":{
        "name":"tool_create_product",
        "description":"Create a new product with optional price and uom.",
        "parameters":{"type":"object","properties":{
            "name":{"type":"string"},
            "list_price":{"type":"number","nullable":True},
            "uom_name":{"type":"string","nullable":True},
            "default_code":{"type":"string","nullable":True}
        },"required":["name"]}
    }},
    {"type":"function","function":{
        "name":"tool_create_partner",
        "description":"Create a new partner/customer/supplier.",
        "parameters":{"type":"object","properties":{
            "name":{"type":"string"},
            "phone":{"type":"string","nullable":True},
            "email":{"type":"string","nullable":True},
            "customer":{"type":"boolean","nullable":True},
            "supplier":{"type":"boolean","nullable":True}
        },"required":["name"]}
    }},
    {"type":"function","function":{
        "name":"tool_create_sale_order",
        "description":"Create a sale order for a customer with a list of product lines.",
        "parameters":{"type":"object","properties":{
            "partner_name":{"type":"string"},
            "lines":{"type":"array","items":{"type":"object","properties":{
                "product_name":{"type":"string"},
                "qty":{"type":"number"},
                "price":{"type":"number","nullable":True}
            },"required":["product_name","qty"]}}
        },"required":["partner_name","lines"]}
    }},
    {"type":"function","function":{
        "name":"tool_sales_summary",
        "description":"Summarize recent sales for a period: today, this_week, or this_month.",
        "parameters":{"type":"object","properties":{
            "period":{"type":"string","enum":["today","this_week","this_month"]}
        },"required":[]}
    }}
]

def _run_tool(tool_call):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")
    if name == "tool_create_product":
        return tool_create_product(**args)
    if name == "tool_create_partner":
        return tool_create_partner(**args)
    if name == "tool_create_sale_order":
        return tool_create_sale_order(**args)
    if name == "tool_sales_summary":
        return tool_sales_summary(**args)
    raise Exception(f"Unknown tool: {name}")

def _chat_complete(messages):
    client = _client()
    try:
        resp = client.chat.completions.create(
            model=_model_name(),
            messages=messages,
            tools=TOOLS_SPEC,
            tool_choice="auto",
            temperature=0.3,
        )
        return resp
    except Exception as e:
        base_url_raw = _get_conf("ai_assistant.openai_base_url") or ""
        hint = ""
        if "console.groq.com" in (base_url_raw or "").lower():
            hint = " Tip: Use https://api.groq.com/openai/v1 as Base URL."
        raise Exception(str(e) + hint)

def _ai_reply(user_text):
    history = _ensure_messages()
    msgs = [{"role":"system","content":SYSTEM_PROMPT}] + history + [{"role":"user","content":user_text}]
    first = _chat_complete(msgs)
    msg = first.choices[0].message
    history.append({"role":"user","content":user_text})
    if msg.tool_calls:
        tool_msgs = []
        for tc in msg.tool_calls:
            try:
                result = _run_tool(tc)
                tool_msgs.append({"role":"tool","tool_call_id":tc.id,"content":json.dumps(result, ensure_ascii=False)})
            except Exception as e:
                tool_msgs.append({"role":"tool","tool_call_id":tc.id,"content":json.dumps({"error":str(e)})})
        follow = _chat_complete(
            [{"role":"system","content":SYSTEM_PROMPT}] + history + [{"role":"assistant","content": msg.content or "", "tool_calls": msg.tool_calls}] + tool_msgs
        )
        final = follow.choices[0].message
        history.append({"role":"assistant","content":final.content or ""})
        return final.content or ""
    else:
        history.append({"role":"assistant","content":msg.content or ""})
        return msg.content or ""

def _html_page(body, title="GPT-5 Assistant"):
    tpl = """<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>{title}</title>
</head>
<body>
<div style="max-width:900px;margin:24px auto;padding:8px;">
<h2>{title}</h2>
{body}
<hr/>
<p><a href="/ai_assistant">Chat</a> • <a href="/ai_assistant/settings">Settings</a> • <a href="/ai_assistant/clear">New chat</a></p>
</div>
<script>
(function(){{
  const micBtn = document.getElementById('mic');
  const input = document.getElementById('msg');
  if (!micBtn || (!window.SpeechRecognition && !window.webkitSpeechRecognition)) return;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SR();
  rec.lang = 'ar-SA';
  rec.continuous = false;
  rec.interimResults = false;
  micBtn.addEventListener('click', function(){{
    rec.start();
  }});
  rec.onresult = function(ev){{
    let t = ev.results[0][0].transcript;
    if (input) {{ input.value = t; }}
  }};
}})();
function speak(text){{
  if (!window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = (/[\\u0600-\\u06FF]/.test(text) ? 'ar-SA' : 'en-US');
  window.speechSynthesis.speak(u);
}}
</script>
</body>
</html>"""
    return tpl.format(title=_html.escape(title), body=body)

class AIAssistantController(http.Controller):

    @http.route(['/ai_assistant', '/ai_assistant/'], type='http', auth='user', methods=['GET','POST'], csrf=False)
    def chat(self, **post):
        history = _ensure_messages()
        answer = ""
        error = ""
        if request.httprequest.method == 'POST':
            user_msg = (post.get('message') or '').strip()
            if user_msg:
                try:
                    answer = _ai_reply(user_msg)
                except Exception as e:
                    error = _html.escape(str(e))
        def render_msg(m):
            role = m.get('role')
            who = "You" if role == "user" else ("Assistant" if role == "assistant" else role)
            content = _html.escape(m.get('content') or "")
            return f"<div><b>{who}:</b><pre style='white-space:pre-wrap'>{content}</pre></div>"
        chat_html = "".join(render_msg(m) for m in history[-30:])
        form = """
        <form method="post" action="/ai_assistant">
            <label>Message</label><br/>
            <textarea id="msg" name="message" rows="3" style="width:100%%" placeholder="اكتب سؤالك هنا / Type your question..."></textarea><br/>
            <button type="submit">Send</button>
            <button type="button" id="mic" title="Voice input (browser)">🎤</button>
        </form>
        """
        if answer:
            form += f"<script>try{{speak({json.dumps(answer)})}}catch(e){{}};</script>"
        body = f"""
        <p style="font-size:90%%">⚠️ Never paste API keys here. Configure them in <a href="/ai_assistant/settings">Settings</a>.</p>
        {chat_html}
        {form}
        """
        if error:
            body = f"<div style='color:red'><b>Error:</b> {error}</div>" + body
        return _html_page(body, "GPT-5 Assistant — Chat")

    @http.route(['/ai_assistant/settings'], type='http', auth='user', methods=['GET','POST'], csrf=False)
    def settings(self, **post):
        msg = ""
        if request.httprequest.method == 'POST':
            if 'api_key' in post:
                _set_conf("ai_assistant.openai_api_key", post.get('api_key') or '')
                msg = "Saved API key."
            if 'base_url' in post:
                _set_conf("ai_assistant.openai_base_url", post.get('base_url') or '')
                if msg: msg += " "
                msg += "Saved Base URL."
            if 'model' in post:
                _set_conf("ai_assistant.model", post.get('model') or 'llama-3.1-70b-versatile')
                if msg: msg += " "
                msg += "Saved Model."
            danger = 'danger' in post and post.get('danger') == 'on'
            _set_conf("ai_assistant.danger_mode", "true" if danger else "false")
            if msg: msg += " "
            msg += ("Enabled" if danger else "Disabled") + " Dangerous/Sudo Mode."
        api_key = _get_conf("ai_assistant.openai_api_key") or ""
        base_url = _get_conf("ai_assistant.openai_base_url") or ""
        model = _get_conf("ai_assistant.model") or "llama-3.1-70b-versatile"
        danger_mode = _danger_mode()
        body = f"""
        <p>Configure your OpenAI-compatible endpoint (Groq defaults).</p>
        <form method="post" action="/ai_assistant/settings">
            <label>API Key</label><br/>
            <input type="password" name="api_key" value="{_html.escape(api_key)}" style="width:100%%"/><br/><br/>
            <label>Custom Base URL (e.g., https://api.groq.com/openai/v1)</label><br/>
            <input type="text" name="base_url" value="{_html.escape(base_url)}" style="width:100%%"/><br/><br/>
            <label>Model</label><br/>
            <input type="text" name="model" value="{_html.escape(model)}" style="width:100%%"/><br/><br/>
            <label><input type="checkbox" name="danger" {"checked" if danger_mode else ""}/> Dangerous/Sudo Mode (perform data-changing actions without explicit confirmation)</label><br/><br/>
            <button type="submit">Save</button>
        </form>
        """
        if msg:
            body = f"<div style='color:green'>{_html.escape(msg)}</div>" + body
        body += """
        <hr/>
        <p><b>Examples</b></p>
        <ul>
          <li>Groq: Base URL: https://api.groq.com/openai/v1, Model: llama-3.1-70b-versatile</li>
          <li>OpenAI: leave Base URL blank, Model: gpt-4o-mini (requires OpenAI key & quota)</li>
          <li>OpenRouter: Base URL: https://openrouter.ai/api/v1, Model: meta-llama/llama-3.1-70b-instruct</li>
        </ul>
        """
        return _html_page(body, "GPT-5 Assistant — Settings")

    @http.route(['/ai_assistant/clear'], type='http', auth='user', methods=['GET'])
    def clear(self, **kw):
        request.session['ai_messages'] = []
        return http.redirect_with_hash('/ai_assistant')
