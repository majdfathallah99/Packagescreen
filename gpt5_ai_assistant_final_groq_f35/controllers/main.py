
# -*- coding: utf-8 -*-
import json
import html as _html
from datetime import datetime
import requests
from odoo import http
from odoo.http import request

TIMEOUT = 30

def _get_conf(key, default=None):
    try:
        return request.env['ir.config_parameter'].sudo().get_param(key, default)
    except Exception:
        return default

def _set_conf(key, val):
    try:
        request.env['ir.config_parameter'].sudo().set_param(key, val or '')
        return True
    except Exception:
        return False

def _normalize_base_url(url):
    if not url:
        return 'https://api.groq.com/openai/v1'
    url = url.strip().rstrip('/')
    if not url:
        return 'https://api.groq.com/openai/v1'
    if url.lower() in ('groq', 'groq.com', 'api.groq.com'):
        return 'https://api.groq.com/openai/v1'
    if not url.endswith('/openai/v1') and url.endswith('/v1'):
        return url
    return url

def _model_name():
    return (_get_conf("ai_assistant.model") or "llama-3.1-8b-instant").strip()

def _env():
    return request.env.sudo()

def tool_create_product(name:str, list_price:float=0.0, uom_name:str="Units", default_code:str=None):
    Product = _env()['product.product']
    Uom = _env()['uom.uom']
    uom = Uom.search([('name','ilike', uom_name)], limit=1)
    vals = {'name': name, 'list_price': float(list_price or 0.0)}
    if uom:
        vals['uom_id'] = uom.id; vals['uom_po_id'] = uom.id
    if default_code:
        vals['default_code'] = default_code
    p = Product.create(vals)
    return {"id": p.id, "name": p.display_name, "price": p.list_price, "uom": uom.name if uom else None}

def tool_create_partner(name:str, phone:str=None, email:str=None, customer:bool=True, supplier:bool=False):
    Partner = _env()['res.partner']
    p = Partner.create({
        'name': name,
        'phone': phone or False,
        'email': email or False,
        'customer_rank': 1 if customer else 0,
        'supplier_rank': 1 if supplier else 0,
    })
    return {"id": p.id, "name": p.display_name, "phone": p.phone, "email": p.email}

def tool_count_products(kind:str="template"):
    if kind == "variant":
        return {"count": _env()['product.product'].search_count([]), "kind":"variant"}
    return {"count": _env()['product.template'].search_count([]), "kind": "template"}

TOOLS = [
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
        "name":"tool_count_products",
        "description":"Count products. Use kind='template' (default) for unique products, or kind='variant' for variants.",
        "parameters":{"type":"object","properties":{
            "kind":{"type":"string","enum":["template","variant"]}
        },"required":[]}
    }},
]

def _chat(messages):
    api_key = _get_conf("ai_assistant.openai_api_key") or ""
    if not api_key:
        raise Exception("API key is not configured. Open /ai_assistant/settings.")
    base = _normalize_base_url(_get_conf("ai_assistant.openai_base_url"))
    url = base.rstrip('/') + "/chat/completions"
    model = _model_name()
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": 0.2, "tools": TOOLS, "tool_choice":"auto"}
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=TIMEOUT)
    if r.status_code >= 400:
        raise Exception(f"LLM error {r.status_code}: {r.text[:500]}")
    data = r.json()
    choice = data["choices"][0]
    message = choice["message"]
    if choice.get("finish_reason") == "tool_calls" and message.get("tool_calls"):
        call = message["tool_calls"][0]
        fn = call["function"]["name"]
        args = json.loads(call["function"].get("arguments") or "{}")
        if fn == "tool_create_product":
            result = tool_create_product(**args)
        elif fn == "tool_create_partner":
            result = tool_create_partner(**args)
        elif fn == "tool_count_products":
            result = tool_count_products(**args)
        else:
            result = {"error":"unknown tool"}
        messages = messages + [message, {"role":"tool","tool_call_id": call["id"], "name": fn, "content": json.dumps(result, ensure_ascii=False)}]
        payload2 = {"model": model, "messages": messages, "temperature": 0.2}
        r2 = requests.post(url, headers=headers, data=json.dumps(payload2), timeout=TIMEOUT)
        if r2.status_code >= 400:
            raise Exception(f"LLM error {r2.status_code}: {r2.text[:500]}")
        return r2.json()["choices"][0]["message"].get("content") or ""
    return message.get("content") or ""

def _safe_session_list(key):
    s = getattr(request, 'session', None)
    if not s:
        return []
    msgs = s.get(key) or []
    if not isinstance(msgs, list):
        msgs = []
    s[key] = msgs
    if hasattr(s, 'modified'):
        s.modified = True
    return msgs

def _page(body, title="GPT-5 Assistant"):
    tpl = """<!doctype html>
<html><head><meta charset="utf-8"/><title>{title}</title></head>
<body>
<div style="max-width:900px;margin:24px auto;padding:8px;">
<h2>{title}</h2>
{body}
<hr/>
<p><a href="/ai_assistant">Chat</a> • <a href="/ai_assistant/settings">Settings</a> • <a href="/ai_assistant/clear">New chat</a> • <a href="/ai_assistant/diag">Diagnostics</a></p>
</div>
<script>
(function(){{
  const micBtn = document.getElementById('mic');
  const input = document.getElementById('msg');
  const vstatus = document.getElementById('vstatus');
  const ttsstatus = document.getElementById('ttsstatus');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  function setStatus(t){{ if(vstatus) vstatus.textContent = t; }}
  function setTTS(t){{ if(ttsstatus) ttsstatus.textContent = t; }}

  function detectLang(s){{ 
    if(!s) return (navigator.language||'en').slice(0,2);
    if(/[\u0600-\u06FF]/.test(s)) return 'ar';
    if(/[\u0400-\u04FF]/.test(s)) return 'ru';
    if(/[\u4E00-\u9FFF]/.test(s)) return 'zh';
    if(/[\u0900-\u097F]/.test(s)) return 'hi';
    if(/[\u3040-\u30FF]/.test(s)) return 'ja';
    if(/[\uAC00-\uD7AF]/.test(s)) return 'ko';
    return 'en';
  }}
  const langMap = {{ar:'ar-SA', en:'en-US', ru:'ru-RU', zh:'zh-CN', hi:'hi-IN', ja:'ja-JP', ko:'ko-KR'}};

  async function loadVoicesOnce(){{ return new Promise((resolve)=>{{
      try{{ const synth = window.speechSynthesis;
        if(!synth){{ resolve([]); return; }}
        let voices = synth.getVoices();
        if(voices && voices.length){{ resolve(voices); return; }}
        const handler = function(){{ voices = synth.getVoices(); if(voices && voices.length){{ synth.removeEventListener('voiceschanged', handler); resolve(voices);}} }};
        synth.addEventListener('voiceschanged', handler);
        setTimeout(()=>resolve(synth.getVoices()||[]), 1000);
      }}catch(e){{ resolve([]); }}
    }});
  }}

  async function pickVoice(lang2){{ const voices = await loadVoicesOnce();
    let v = voices.find(v=>v.lang && v.lang.toLowerCase().startsWith(lang2));
    if(!v){{ const target = langMap[lang2] || 'en-US';
      v = voices.find(v=>v.lang===target) || voices.find(v=>v.lang && v.lang.toLowerCase().startsWith(target.slice(0,2)));
    }}
    return v || null;
  }}

  async function speak(text){{ try{{
      if(!window.speechSynthesis){{ setTTS('No speechSynthesis'); return null; }}
      const lang2 = detectLang(text||'');
      const u = new SpeechSynthesisUtterance(text||'');
      const v = await pickVoice(lang2);
      if(v) u.voice = v;
      u.lang = (v && v.lang) || (langMap[lang2]||'en-US');
      setTTS('Speaking…');
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
      u.onend = function(){{ setTTS(''); }};
      u.onerror = function(){{ setTTS('TTS error'); }};
      return u;
    }}catch(e){{ setTTS('TTS failed'); return null; }}
  }}

  window.speakLast = function(){{ try{{
    const ta = document.getElementById('last_assistant_text');
    const txt = ta ? (ta.value||'').trim() : '';
    if(txt) speak(txt);
  }}catch(e){{}} }};

  try{{ 
    const ta = document.getElementById('last_assistant_text');
    const txt = ta ? (ta.value||'').trim() : '';
    if(txt){{
      const key='ai_last_spoken';
      const hash = Array.from(txt).reduce((a,c)=>((a*31 + c.charCodeAt(0))>>>0),0);
      if(window.sessionStorage.getItem(key) != String(hash)){{ window.sessionStorage.setItem(key,String(hash)); speak(txt); }}
    }}
  }}catch(e){{}}

  if (micBtn && SR) {{
    micBtn.addEventListener('click', function(){{ 
      try{{ 
        const rec = new SR(); 
        rec.lang = (navigator.language||'en-US');
        setStatus('Listening…');
        rec.onresult = function(ev){{ try{{ const t = ev.results[ev.resultIndex][0].transcript || ''; if(input) input.value = t; }}catch(e){{}} }};
        rec.onend = function(){{ setStatus(''); }};
        rec.start();
      }}catch(e){{ alert('Mic error'); }}
    }});
  }}

  let recog = null;
  function autoSend(){{ 
    try{{ var form = document.querySelector('form[action=\"/ai_assistant\"]');
      if(!form) return;
      var fd = new FormData(form);
      fetch('/ai_assistant', {{method:'POST', body:fd, credentials:'same-origin'}})
        .then(function(){{ location.reload(); }});
    }}catch(e){{}}
  }}
  window.startLive = function(){{
    const SRx = window.SpeechRecognition || window.webkitSpeechRecognition;
    if(!SRx){{ alert('Your browser does not support voice input.'); return; }}
    window.__liveActive = true; setStatus('Listening…');
    try{{
      if(recog){{ try{{ recog.stop(); }}catch(e){{}} recog=null; }}
      recog = new SRx(); recog.lang=(navigator.language||'en-US'); recog.continuous=true; recog.interimResults=true;
      let partial = '';
      recog.onresult = function(ev){{ try{{ for(let i=ev.resultIndex;i<ev.results.length;i++){{ const r=ev.results[i]; if(r.isFinal){{ const t=r[0].transcript||''; if(input) input.value = t; autoSend(); }} else {{ partial = r[0].transcript||''; }} }} if(input && partial) input.placeholder = partial; }}catch(e){{}} }};
      recog.onerror = function(){{ setStatus('Mic error'); }};
      recog.onend = function(){{ if(window.__liveActive){{ try{{ recog.start(); }}catch(e){{}} }} else {{ setStatus(''); }} }};
      recog.start();
    }}catch(e){{ setStatus('Mic blocked'); }}
  }};
  window.stopLive = function(){{ window.__liveActive=false; try{{ recog && recog.stop(); }}catch(e){{}} setStatus(''); }};
}})();
</script>
</body></html>
"""
    return tpl.format(title=_html.escape(title), body=body)

class AIAssistantController(http.Controller):

    @http.route(['/ai_assistant'], type='http', auth='user', methods=['GET','POST'], csrf=False)
    def chat(self, **post):
        error = ""
        history = _safe_session_list('ai_messages')
        user_text = (post.get('message') or "").strip() if post else ""
        last_assistant = ""
        if request.httprequest.method == 'POST' and user_text:
            history.append({"role":"user","content": user_text})
            try:
                reply = _chat(history[:])
            except Exception as e:
                error = str(e)
                reply = ""
            if reply:
                history.append({"role":"assistant","content": reply})
                last_assistant = reply

        def fmt(msg):
            role = msg.get('role')
            content = _html.escape(msg.get('content') or "")
            if role == 'user':
                return f"<p><b>You:</b><br/>{content}</p>"
            elif role == 'assistant':
                return f"<p><b>Assistant:</b><br/>{content}</p>"
            elif role == 'tool':
                return f"<pre style='background:#f6f6f6;padding:8px;border:1px solid #ddd;white-space:pre-wrap'>{content}</pre>"
            else:
                return f"<p><i>{role}</i>: {content}</p>"

        conv = "\n".join(fmt(m) for m in history[-100:])  # show more history
        body = f"""
<form method="post" action="/ai_assistant">
  <div style="margin-bottom:12px">{conv or '<i>No messages yet.</i>'}</div>
  <textarea id="msg" name="message" placeholder="اكتب سؤالك هنا / Type your question..." style="width:100%;height:70px"></textarea><br/>
  <div style="margin-top:6px">
    <button type="submit">Send</button>
    <button type="button" id="mic">🎤</button>
    <button type="button" id="live" onclick="startLive()">Live</button>
    <button type="button" id="stop" onclick="stopLive()">Stop</button>
    <button type="button" id="speak_last" onclick="speakLast()">🔊 Speak last</button>
    <span id="vstatus" style="margin-left:8px;color:#666"></span>
    <span id="ttsstatus" style="margin-left:8px;color:#666"></span>
  </div>
  <textarea id="last_assistant_text" style="display:none">{_html.escape(last_assistant)}</textarea>
</form>
"""
        if error:
            body = f"<div style='color:red'><b>Error:</b> {_html.escape(error)}</div>" + body
        return _page(body, "GPT-5 Assistant — Chat")

    @http.route(['/ai_assistant/settings'], type='http', auth='user', methods=['GET','POST'], csrf=False)
    def settings(self, **post):
        msg = ""
        if request.httprequest.method == 'POST' and post:
            if 'api_key' in post:
                _set_conf("ai_assistant.openai_api_key", post.get('api_key') or '')
                msg = "Saved API key."
            if 'base_url' in post:
                _set_conf("ai_assistant.openai_base_url", post.get('base_url') or '')
                msg = (msg + " " if msg else "") + "Saved Base URL."
            if 'model' in post:
                _set_conf("ai_assistant.model", post.get('model') or '')
                msg = (msg + " " if msg else "") + "Saved model."
        api_key = _get_conf("ai_assistant.openai_api_key") or ""
        base_url = _get_conf("ai_assistant.openai_base_url") or ""
        configured_model = _get_conf("ai_assistant.model") or ""
        body = f"""
<p>Configure your OpenAI-compatible endpoint (Groq defaults).</p>
<form method="post" action="/ai_assistant/settings">
  <label>API Key</label><br/>
  <input type="password" name="api_key" value="{_html.escape(api_key)}" style="width:100%"/><br/><br/>
  <label>Custom Base URL (e.g., https://api.groq.com/openai/v1)</label><br/>
  <input type="text" name="base_url" value="{_html.escape(base_url)}" style="width:100%"/><br/><br/>
  <label>Model (e.g., llama-3.1-8b-instant)</label><br/>
  <input type="text" name="model" value="{_html.escape(configured_model)}" style="width:100%"/><br/><br/>
  <button type="submit">Save</button>
</form>
"""
        if msg:
            body = f"<div style='color:green'>{_html.escape(msg)}</div>" + body
        return _page(body, "GPT-5 Assistant — Settings")

    @http.route(['/ai_assistant/clear'], type='http', auth='user', methods=['GET'])
    def clear(self, **kw):
        try:
            request.session['ai_messages'] = []
            if hasattr(request.session, 'modified'):
                request.session.modified = True
        except Exception:
            pass
        return request.redirect('/ai_assistant')

    @http.route(['/ai_assistant/diag'], type='http', auth='user', methods=['GET','POST'], csrf=False)
    def diag(self, **post):
        base_url = _normalize_base_url(_get_conf("ai_assistant.openai_base_url"))
        configured_model = _get_conf("ai_assistant.model") or ""
        model = _model_name()
        reply = ""
        err = ""
        if request.httprequest.method == 'POST':
            try:
                api_key = _get_conf("ai_assistant.openai_api_key") or ""
                url = base_url.rstrip('/') + "/chat/completions"
                headers = {"Authorization":"Bearer "+api_key, "Content-Type":"application/json"}
                payload = {"model": model, "messages":[{"role":"user","content":"ping"}], "max_tokens": 8, "temperature":0}
                r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=TIMEOUT)
                if r.status_code >= 400:
                    err = f"{r.status_code}: {r.text[:300]}"
                else:
                    reply = (r.json()["choices"][0]["message"]["content"] or "").strip()
            except Exception as e:
                err = str(e)
        body = f"""
<p><b>Effective Base URL:</b> {_html.escape(base_url or '')}</p>
<p><b>Configured Model:</b> {_html.escape(configured_model)}</p>
<p><b>Effective Model:</b> {_html.escape(model)}</p>
<form method="post" action="/ai_assistant/diag"><button type="submit">Run ping test</button></form>
"""
        if reply:
            body += f"<div style='color:green'><b>Ping OK:</b> {_html.escape(reply)}</div>"
        if err:
            body += f"<div style='color:red'><b>Error:</b> {_html.escape(err)}</div>"
        return _page(body, "GPT-5 Assistant — Diagnostics")
