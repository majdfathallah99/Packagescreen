# -*- coding: utf-8 -*-
import json
import html as _html
import re
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
CRITICAL: Only call tool_create_product when the user asks you to CREATE a product.
If the user asks for a COUNT like "how many products do I have", call tool_count_products.
If a tool validation error occurs, fix your arguments and retry once with correct JSON.
"""

AFFIRMATIVE_PATTERNS = {
    "yes","y","yeah","yep","sure","ok","okay","confirm","go ahead","do it",
    "نعم","ايه","أيوه","تمام","أوافق","نفذ","نفّذ","أكيد","أجل","طيب"
}

def _get_conf(key, default=False):
    return request.env['ir.config_parameter'].sudo().get_param(key, default)

def _set_conf(key, value):
    request.env['ir.config_parameter'].sudo().set_param(key, value)

def _normalize_base_url(url):
    if not url:
        return "https://api.groq.com/openai/v1"
    u = (url or "").strip()
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
    return OpenAI(api_key=api_key, base_url=base_url)

def _danger_mode():
    v = (_get_conf("ai_assistant.danger_mode") or "false").lower()
    return v in ("1","true","yes","on")

def _env(danger=False):
    env = request.env
    if danger:
        try:
            return env.sudo()
        except Exception:
            try:
                return env.with_user(1)
            except Exception:
                return env
    return env

def _danger_system_note():
    if _danger_mode():
        return {"role": "system", "content": (
            "Dangerous/Sudo Mode is ENABLED. Execute any data-changing request "
            "(create/update/delete, buy/sell) immediately without asking for confirmation. "
            "Use sudo-level ORM when needed. Keep replies concise."
        )}
    return {"role": "system", "content": (
        "Dangerous/Sudo Mode is DISABLED. Ask for explicit confirmation before changing data."
    )}

def _normalize_model(name):
    n = (name or "").strip()
    if not n or n.lower() == "auto":
        return "llama-3.3-70b-versatile"
    if n == "llama-3.1-70b-versatile":
        return "llama-3.3-70b-versatile"
    return n

def _model_name():
    configured = _get_conf("ai_assistant.model") or ""
    return _normalize_model(configured)

def _currency_symbol():
    company = request.env.company
    return company.currency_id.symbol if company and company.currency_id else "$"

def _ensure_messages():
    if 'ai_messages' not in request.session:
        request.session['ai_messages'] = []
    return request.session['ai_messages']

def _is_affirmative(text:str) -> bool:
    t = (text or "").strip().lower()
    return (t in AFFIRMATIVE_PATTERNS) or any(tok in t for tok in AFFIRMATIVE_PATTERNS)

def _persist_history(history):
    try:
        request.session['ai_messages'] = history
        if hasattr(request.session, 'modified'):
            request.session.modified = True
    except Exception:
        request.session['ai_messages'] = list(history or [])

def _assistant_was_confirming() -> bool:
    history = _ensure_messages(); _persist_history(history)
    if not history:
        return False
    last = (history[-1].get("content") or "").lower()
    confirm_cues = ["confirm", "are you sure", "تأكيد", "هل أنت متأكد", "هل تريد", "هل تريد المتابعة"]
    return any(k in last for k in confirm_cues)

# ---- Tool implementations ----

def tool_create_product(name:str, list_price:float=0.0, uom_name:str="Units", default_code:str=None):
    env = _env(_danger_mode())
    Product = env['product.product']
    Uom = env['uom.uom']
    uom = Uom.search([('name','ilike', uom_name)], limit=1)
    vals = {'name': name, 'list_price': float(list_price or 0.0)}
    if uom:
        vals['uom_id'] = uom.id
        vals['uom_po_id'] = uom.id
    if default_code:
        vals['default_code'] = default_code
    p = Product.create(vals)
    return {"id": p.id, "name": p.display_name, "price": p.list_price, "uom": uom.name if uom else None}

def tool_create_partner(name:str, phone:str=None, email:str=None, customer:bool=True, supplier:bool=False):
    env = _env(_danger_mode())
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
    env = _env(_danger_mode())
    Partner = env['res.partner']
    partner = Partner.search([('name','ilike', name)], limit=1)
    if not partner:
        raise Exception(f"Partner '{name}' not found.")
    return partner

def _find_product_by_name(name):
    env = _env(_danger_mode())
    Product = env['product.product']
    product = Product.search([('name','ilike', name)], limit=1)
    if not product:
        raise Exception(f"Product '{name}' not found.")
    return product

def tool_create_sale_order(partner_name:str, lines:list):
    env = _env(_danger_mode())
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

def tool_count_products(kind: str = "template"):
    env = request.env
    if (kind or '').lower() == 'variant':
        return {"kind": "variant", "count": env['product.product'].search_count([])}
    return {"kind": "template", "count": env['product.template'].search_count([])}

def fields_now():
    try:
        return request.env['ir.fields.converter'].context_timestamp(request.env.user, datetime.utcnow())
    except Exception:
        return datetime.utcnow()

TOOLS_SPEC = [
    {"type":"function","function":{
        "name":"tool_count_products",
        "description":"Count products. Default kind='template' (unique products). Use kind='variant' for variants.",
        "parameters":{"type":"object","properties":{
            "kind":{"type":"string","enum":["template","variant"]}
        },"required":[]}
    }},
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
    if name == "tool_count_products":
        return tool_count_products(**args)
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

def _maybe_server_shortcut(user_text:str):
    t = (user_text or '').strip().lower()
    if re.search(r'\bhow\s+many\s+(products|items)\b', t):
        data = tool_count_products(kind='template')
        return f"You have {data['count']} products (unique templates)."
    if ('كم' in t and 'منتج' in t) or ('عدد' in t and 'المنتجات' in t):
        data = tool_count_products(kind='template')
        return f"لديك {data['count']} منتج (قوالب فريدة)."
    return None

def _ai_reply(user_text):
    history = _ensure_messages(); _persist_history(history)
    short = _maybe_server_shortcut(user_text)
    if short:
        history.append({"role":"user","content":user_text}); _persist_history(history)
        history.append({"role":"assistant","content":short})
        return short

    extra_msgs = []
    if _is_affirmative(user_text) and _assistant_was_confirming():
        extra_msgs.append({"role":"system","content":"User already confirmed. Execute the previously discussed action now without re-asking."})

    msgs = [{"role":"system","content":SYSTEM_PROMPT}, _danger_system_note()] + extra_msgs + history + [{"role":"user","content":user_text}]
    first = _chat_complete(msgs)
    msg = first.choices[0].message
    history.append({"role":"user","content":user_text}); _persist_history(history)
    if getattr(msg, "tool_calls", None):
        tool_msgs = []
        for tc in msg.tool_calls:
            try:
                result = _run_tool(tc)
                tool_msgs.append({"role":"tool","tool_call_id":tc.id,"content":json.dumps(result, ensure_ascii=False)})
            except Exception as e:
                tool_msgs.append({"role":"tool","tool_call_id":tc.id,"content":json.dumps({"error":str(e)})})
        follow = _chat_complete(
            [{"role":"system","content":SYSTEM_PROMPT}, _danger_system_note()] + history + [{"role":"assistant","content": msg.content or "", "tool_calls": msg.tool_calls}] + tool_msgs
        )
        final = follow.choices[0].message
        content = (final.content or "").strip()
        if not content:
            summary_chunks = []
            for tm in tool_msgs:
                try:
                    data = json.loads(tm.get("content") or "{}")
                    if isinstance(data, dict) and data.get("error"):
                        summary_chunks.append("❌ " + str(data.get("error")))
                    else:
                        summary_chunks.append("✅ " + json.dumps(data, ensure_ascii=False))
                except Exception:
                    c = tm.get("content") or ""
                    summary_chunks.append("ℹ️ " + (c if len(c) < 500 else c[:500] + "…"))
            content = "\n".join([c for c in summary_chunks if c]) or "✅ Done."
        history.append({"role":"assistant","content":content})
        if len(history) > 1000:
            history[:] = history[-1000:]
        _persist_history(history)
        return content
    else:
        content = (msg.content or "").strip() or "🤖 (No text returned)"
        history.append({"role":"assistant","content":content})
        if len(history) > 1000:
            history[:] = history[-1000:]
        _persist_history(history)
        return content

def _html_page(body, title="GPT-5 Assistant"):
    # Use plain token replacement to avoid formatting collisions with % or { } in JS/CSS.
    tpl = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>__TITLE__</title>
</head>
<body>
<div style="max-width:900px;margin:24px auto;padding:8px;">
<h2>__TITLE__</h2>
__BODY__
<hr/>
<p><a href="/ai_assistant">Chat</a> • <a href="/ai_assistant/settings">Settings</a> • <a href="/ai_assistant/clear">New chat</a> • <a href="/ai_assistant/diag">Diagnostics</a> • <a href="/ai_assistant/export">Export</a></p>
</div>
<script>(function(){
  // ---- Voice helpers ----
  function detectLang(s){
    if(!s) return (navigator.language||'en').slice(0,2);
    if(/[\\u0600-\\u06FF]/.test(s)) return 'ar';
    if(/[\\u0400-\\u04FF]/.test(s)) return 'ru';
    if(/[\\u4E00-\\u9FFF]/.test(s)) return 'zh';
    if(/[\\u0900-\\u097F]/.test(s)) return 'hi';
    if(/[\\u3040-\\u30FF]/.test(s)) return 'ja';
    if(/[\\uAC00-\\uD7AF]/.test(s)) return 'ko';
    return 'en';
  }
  function pickVoice(lang2){
    try{
      const voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
      const pref = {ar:'ar',zh:'zh',hi:'hi',ja:'ja',ko:'ko',ru:'ru',en:'en'};
      const tgt = pref[lang2] || 'en';
      let v = null;
      for (const vv of voices){
        const l=(vv.lang||'').toLowerCase(), n=(vv.name||'').toLowerCase();
        if(l.startsWith(tgt) || (tgt==='ar' && n.includes('arab'))) { v = vv; break; }
        if(!v && (l.includes(tgt)||n.includes(tgt))) v = vv;
      }
      return v || voices[0] || null;
    }catch(e){ return null; }
  }
  function waitVoices(){
    return new Promise(function(resolve){
      if(!window.speechSynthesis){ resolve(); return; }
      const have = window.speechSynthesis.getVoices();
      if (have && have.length){ resolve(); return; }
      const t = setInterval(function(){
        const vv = window.speechSynthesis.getVoices();
        if (vv && vv.length){ clearInterval(t); resolve(); }
      }, 120);
      setTimeout(function(){ try{clearInterval(t);}catch(e){} resolve(); }, 1500);
    });
  }
  let ttsSpeaking = false;
  async function speak(text){
    if(!window.speechSynthesis) return null;
    try{ window.speechSynthesis.cancel(); }catch(e){}
    await waitVoices();
    const lang2 = detectLang(text||'');
    const u = new SpeechSynthesisUtterance(text||'');
    const v = pickVoice(lang2);
    if(v){ u.voice=v; u.lang=v.lang; } else { u.lang = (lang2==='ar'?'ar-SA':'en-US'); }
    u.rate = 1.0; u.pitch = 1.0;
    u.onstart = function(){ ttsSpeaking = true; };
    u.onend   = function(){ ttsSpeaking = false; try{ window.__resumeAfterTTS && window.__resumeAfterTTS(); }catch(e){} };
    window.speechSynthesis.speak(u);
    return u;
  }
  window.speak = speak;

  // ---- Chat wiring (works on the /ai_assistant page) ----
  const micBtn  = document.getElementById('mic');
  const liveBtn = document.getElementById('live');
  const stopBtn = document.getElementById('stop');
  const vstatus = document.getElementById('vstatus');
  const input   = document.getElementById('msg');
  const logEl   = document.getElementById('log');
  const form    = document.getElementById('ai_form');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;

  function setStatus(t){ if(vstatus) vstatus.textContent = t; }
  function append(who, txt){
    if(!logEl) return;
    const div = document.createElement('div');
    div.innerHTML = '<b>'+who+':</b><pre style="white-space:pre-wrap"></pre>';
    div.querySelector('pre').textContent = txt || '';
    logEl.appendChild(div); logEl.scrollTop = logEl.scrollHeight;
  }
  function dedupe(s){
    s = (s||'').replace(/\\s+/g,' ').trim();
    s = s.replace(/\\b(\\w+)(\\s+\\1\\b)+/gi,'$1');
    if(s.length>4 && s.length%2===0){
      const h=s.slice(0,s.length/2);
      if((h+h).toLowerCase()===s.toLowerCase()) s=h;
    }
    return s;
  }
  async function sendAjax(text){
    append('You', text);
    try{
      const r = await fetch('/ai_assistant/api/send', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({message:text})
      });
      const raw = await r.json();
      const data = (raw && typeof raw==='object' && 'result' in raw) ? raw.result : raw;

      let replyText = '(no reply)';
      if (data && typeof data.reply === 'string') {
        replyText = data.reply;
      } else if (data && data.error) {
        replyText = '⚠ ' + data.error;
      }
      append('Assistant', replyText);
      if (data && data.reply) {
        const wasLive = window.__liveActive === true;
        window.__liveActive = false; // pause ASR while TTS
        await speak(data.reply);
        window.__resumeAfterTTS = function(){ if(wasLive) startLive(true); };
      }
    }catch(e){
      append('Assistant','⚠ network error');
    }
  }

  if (form){
    form.addEventListener('submit', function(ev){
      ev.preventDefault();
      const t = (input.value||'').trim();
      if(!t) return;
      input.value = '';
      sendAjax(t);
    });
  }

  // Quick mic
  if (micBtn && SR){
    try{
      const rec = new SR();
      rec.lang = (navigator.language||'en-US'); rec.continuous = false; rec.interimResults = true;
      let finalText = '', interim = '';
      micBtn.addEventListener('click', function(){
        if (!window.isSecureContext) { alert('Voice input requires HTTPS.'); return; }
        try{ setStatus('Listening…'); finalText=''; interim=''; rec.start(); }catch(e){ setStatus(''); }
      });
      rec.onresult = function(ev){
        for(let i=ev.resultIndex;i<ev.results.length;i++){
          const r = ev.results[i], t=r[0].transcript;
          if(r.isFinal) finalText += ' ' + t; else interim = t;
        }
        if (input) input.value = dedupe((finalText + ' ' + interim).trim());
      };
      rec.onerror = function(){ setStatus('Mic error'); };
      rec.onend = function(){ setStatus(''); };
    }catch(e){}
  } else if (micBtn && !SR){
    micBtn.addEventListener('click', function(){ alert('Voice input not supported in this browser.'); });
  }

  // Live mic (continuous)
  let recog = null;
  window.__liveActive = false;

  function startLive(){
    if(!SR){ setStatus('speech API not supported'); return; }
    if (!window.isSecureContext) { alert('Live voice requires HTTPS.'); return; }
    window.__liveActive = true;
    if(recog){ try{recog.stop();}catch(e){} recog=null; }
    recog = new SR();
    recog.continuous = true; recog.interimResults = true;
    recog.lang = (navigator.language||'en-US');
    let finalText = '', interim = '';
    recog.onstart = function(){ setStatus('listening…'); };
    recog.onerror = function(){ setStatus('error'); };
    recog.onend   = function(){
      setStatus(window.__liveActive ? 'restarting…' : 'idle');
      if(window.__liveActive){ try{recog.start();}catch(e){} }
    };
    recog.onresult = function(ev){
      if(window.speechSynthesis && window.speechSynthesis.speaking) return;
      for(let i=ev.resultIndex;i<ev.results.length;i++){
        const r = ev.results[i], t=r[0].transcript;
        if(r.isFinal) finalText += ' ' + t; else interim = t;
      }
      input.value = dedupe((finalText + ' ' + interim).trim());
      const last = ev.results[ev.results.length-1];
      if(last && last.isFinal){
        const out = dedupe(finalText).trim();
        if(out){
          try{recog.stop();}catch(e){}
          input.value = out; finalText=''; interim='';
          sendAjax(out);
        }
      }
    };
    try{ recog.start(); }catch(e){}
  }
  function stopLive(){ window.__liveActive=false; if(recog){ try{recog.stop();}catch(e){} } setStatus('stopped'); }
  window.startLive = startLive; window.stopLive = stopLive;
  if (liveBtn) liveBtn.addEventListener('click', startLive);
  if (stopBtn) stopBtn.addEventListener('click', stopLive);

})();</script>
</body></html>"""
    return tpl.replace("__TITLE__", _html.escape(title)).replace("__BODY__", body)

class AIAssistantController(http.Controller):

    @http.route(['/ai_assistant/export'], type='http', auth='user', methods=['GET'])
    def export(self, **kw):
        history = request.session.get('ai_messages') or []
        lines = []
        for m in history:
            role = m.get('role') or ''
            content = m.get('content') or ''
            lines.append(f"{role.upper()}: {content}".replace('\r','').replace('\n','\n'))
        payload = "\n\n".join(lines)
        headers = [
            ('Content-Type', 'text/plain; charset=UTF-8'),
            ('Content-Disposition', 'attachment; filename="ai_chat_transcript.txt"')
        ]
        return request.make_response(payload, headers=headers)

    @http.route(['/ai_assistant', '/ai_assistant/'], type='http', auth='user', methods=['GET','POST'], csrf=False)
    def chat(self, **post):
        history = _ensure_messages(); _persist_history(history)
        err = ""
        if request.httprequest.method == 'POST':
            user_msg = (post.get('message') or '').strip()
            if user_msg:
                try:
                    _ = _ai_reply(user_msg)
                except Exception as e:
                    err = _html.escape(str(e))

        def render_msg(m):
            role = m.get('role')
            who = "You" if role == "user" else ("Assistant" if role == "assistant" else role)
            content = _html.escape(m.get('content') or "")
            return f"<div><b>{who}:</b><pre style='white-space:pre-wrap'>{content}</pre></div>"

        chat_html = "".join(render_msg(m) for m in history)
        form = """
        <form id="ai_form" method="post" action="/ai_assistant">
            <label>Message</label><br/>
            <textarea id="msg" name="message" rows="3" style="width:100%%" placeholder="اكتب سؤالك هنا / Type your question..."></textarea><br/>
            <button type="submit" id="send_btn">Send</button>
            <button type="button" id="mic" title="Voice input (browser)">🎤</button>
            <button type="button" id="live" title="Live voice chat (continuous)">🎙 Live</button>
            <button type="button" id="stop" title="Stop listening">⏹ Stop</button>
            <span id="vstatus" style="font-size:90%%"></span>
        </form>
        """
        body = f"""
        <p style="font-size:90%%">⚠️ Never paste API keys here. Configure them in <a href="/ai_assistant/settings">Settings</a>.</p>
        <div id="log" style="max-height:70vh;overflow-y:auto;border:1px solid #ccc;padding:8px;margin:8px 0;">{chat_html}</div>
        {form}
        """
        if err:
            body = f"<div style='color:red'><b>Error:</b> {err}</div>" + body
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
                _set_conf("ai_assistant.model", post.get('model') or 'auto')
                if msg: msg += " "
                msg += "Saved Model."
            danger = 'danger' in post and post.get('danger') == 'on'
            _set_conf("ai_assistant.danger_mode", "true" if danger else "false")
            if msg: msg += " "
            msg += ("Enabled" if danger else "Disabled") + " Dangerous/Sudo Mode."
            if 'reset' in post:
                _set_conf("ai_assistant.model", "")
                _set_conf("ai_assistant.openai_base_url", "")
                if msg: msg += " "
                msg += "Reset to defaults."
        api_key = _get_conf("ai_assistant.openai_api_key") or ""
        base_url = _get_conf("ai_assistant.openai_base_url") or ""
        configured_model = _get_conf("ai_assistant.model") or "auto"
        effective_model = _normalize_model(configured_model)
        danger_mode = _danger_mode()
        body = f"""
        <p>Configure your OpenAI-compatible endpoint (Groq defaults).</p>
        <form method="post" action="/ai_assistant/settings">
            <label>API Key</label><br/>
            <input type="password" name="api_key" value="{_html.escape(api_key)}" style="width:100%%"/><br/><br/>
            <label>Custom Base URL (e.g., https://api.groq.com/openai/v1)</label><br/>
            <input type="text" name="base_url" value="{_html.escape(base_url)}" style="width:100%%"/><br/><br/>
            <label>Model (configured)</label><br/>
            <input type="text" name="model" value="{_html.escape(configured_model)}" style="width:100%%"/><br/>
            <small>Effective model used: <b>{_html.escape(effective_model)}</b></small><br/><br/>
            <label><input type="checkbox" name="danger" {"checked" if danger_mode else ""}/> Dangerous/Sudo Mode (perform data-changing actions without explicit confirmation)</label><br/><br/>
            <button type="submit">Save</button>
            <button type="submit" name="reset" value="1">Reset defaults</button>
        </form>
        """
        if msg:
            body = f"<div style='color:green'>{_html.escape(msg)}</div>" + body
        body += """
        <hr/>
        <p><b>Examples</b></p>
        <ul>
          <li>Groq: Base URL: https://api.groq.com/openai/v1, Model: llama-3.3-70b-versatile</li>
          <li>OpenAI: leave Base URL blank, Model: gpt-4o-mini</li>
          <li>OpenRouter: Base URL: https://openrouter.ai/api/v1, Model: meta-llama/llama-3.1-70b-instruct</li>
        </ul>
        """
        return _html_page(body, "GPT-5 Assistant — Settings")

    @http.route(['/ai_assistant/clear'], type='http', auth='user', methods=['GET'])
    def clear(self, **kw):
        try:
            request.session.pop('ai_messages', None)
        except Exception:
            request.session['ai_messages'] = []
        return request.redirect('/ai_assistant')

    @http.route(['/ai_assistant/diag'], type='http', auth='user', methods=['GET','POST'], csrf=False)
    def diag(self, **post):
        base_url = _normalize_base_url(_get_conf("ai_assistant.openai_base_url"))
        configured_model = _get_conf("ai_assistant.model") or "auto"
        effective_model = _normalize_model(configured_model)
        danger_mode = _danger_mode()
        reply = ""
        err = ""
        if request.httprequest.method == 'POST':
            try:
                c = _client()
                ping = c.chat.completions.create(
                    model=effective_model,
                    messages=[{"role":"user","content":"ping"}],
                    max_tokens=8,
                    temperature=0
                )
                reply = (ping.choices[0].message.content or "").strip()
            except Exception as e:
                err = str(e)
        body = f"""
        <p><b>Effective Base URL:</b> {_html.escape(base_url or '')}</p>
        <p><b>Configured Model:</b> {_html.escape(configured_model)}</p>
        <p><b>Effective Model:</b> {_html.escape(effective_model)}</p>
        <p><b>Dangerous/Sudo Mode:</b> {"ON" if danger_mode else "OFF"}</p>
        <form method="post" action="/ai_assistant/diag"><button type="submit">Run ping test</button></form>
        """
        if reply:
            body += f"<div style='color:green'><b>Ping OK:</b> {_html.escape(reply)}</div>"
        if err:
            body += f"<div style='color:red'><b>Error:</b> {_html.escape(err)}</div>"
        return _html_page(body, "GPT-5 Assistant — Diagnostics")


class AIAssistantLiveController(http.Controller):

    @http.route(['/ai_assistant/api/send'], type='json', auth='user', methods=['POST'], csrf=False)
    def api_send(self, **post):
        """
        Accept JSON-RPC and plain JSON:
        - JSON-RPC: {"jsonrpc":"2.0","method":"call","params":{"message":"..."}}
        - Plain:    {"message":"..."}
        """
        payload = {}
        try:
            payload = request.jsonrequest or {}
        except Exception:
            payload = {}
        if isinstance(payload, dict) and 'params' in payload and isinstance(payload['params'], dict):
            payload = payload['params']
        if isinstance(post, dict) and post:
            payload = {**payload, **post}
        if not payload:
            try:
                raw = (request.httprequest.data or b'').decode('utf-8', 'ignore')
                if raw:
                    maybe = json.loads(raw)
                    if isinstance(maybe, dict):
                        payload = maybe.get('params', maybe)
            except Exception:
                pass

        msg = (payload.get('message') or '').strip()
        if not msg:
            return {'ok': False, 'error': 'empty'}
        try:
            reply = _ai_reply(msg)
            return {'ok': True, 'reply': reply}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    @http.route(['/ai_assistant/live_chat'], type='http', auth='user', methods=['GET'], csrf=False)
    def live_chat(self, **kw):
        html = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Assistant — Live</title></head>
<body>
<h2>Live Voice Chat</h2>
<p>Open <a href="/ai_assistant">Chat</a> for the full interface.</p>
</body></html>'''
        return request.make_response(html, headers=[('Content-Type','text/html; charset=utf-8')])
