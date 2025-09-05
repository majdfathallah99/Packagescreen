# -*- coding: utf-8 -*-
import json
import re
import requests
from odoo import http
from odoo.http import request

def _get_param(key, default=None):
    icp = request.env['ir.config_parameter'].sudo()
    return icp.get_param(key, default)

def _groq_chat_reply(prompt_text):
    # Read settings (with safe defaults)
    base_url = _get_param('ai_assistant.base_url', 'https://api.groq.com/openai/v1')
    api_key  = _get_param('ai_assistant.api_key')
    model    = _get_param('ai_assistant.model', 'llama-3.1-8b-instant')
    system   = _get_param('ai_assistant.system',
                          'You are an Odoo assistant. Answer briefly and helpfully.')

    if not api_key:
        return ('ERROR: Missing API key (ai_assistant.api_key). '
                'Set it in Settings ▸ Technical ▸ System Parameters.')

    url = base_url.rstrip('/') + '/chat/completions'
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt_text},
        ],
        'temperature': 0.4,
        'stream': False,
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    except Exception as e:
        return 'ERROR: HTTP error reaching Groq endpoint: {0}'.format(e)

    if resp.status_code >= 400:
        # Try to extract a readable error from Groq error shape
        try:
            err = resp.json()
            msg = err.get('error', {}).get('message') or str(err)
        except Exception:
            msg = resp.text
        return 'ERROR: {0} ({1})'.format(msg, resp.status_code)

    try:
        data = resp.json()
    except Exception:
        return 'ERROR: Non-JSON response from model: {0}'.format(resp.text[:400])

    # Robust content extraction: message.content or text (both supported by Groq compat)
    try:
        choice = data.get('choices', [{}])[0]
        content = None
        if isinstance(choice, dict):
            msg = choice.get('message') or {}
            content = (msg.get('content') if isinstance(msg, dict) else None) or choice.get('text')
        if not content:
            return 'ERROR: Model returned no content.'
        return content.strip()
    except Exception as e:
        return 'ERROR: Failed to parse model response: {0}'.format(e)

_HTML = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Live Voice Chat</title>
</head>
<body>
<h2>Live Voice Chat</h2>
<div id="micstate">Mic: idle</div>
<pre id="log" style="height:400px; overflow:auto; border:1px solid #ccc; padding:8px;"></pre>
<form onsubmit="sendText(); return false;" style="margin-top:6px;">
  <input id="q" type="text" placeholder="Type or speak..." style="width:70%;">
  <button type="submit">Send</button>
  <button type="button" onclick="startLive()">Live</button>
  <button type="button" onclick="stopLive()">Stop</button>
</form>

<script>
var logEl = document.getElementById('log');
var qEl   = document.getElementById('q');
var micEl = document.getElementById('micstate');

function append(role, text) {
  if (!text) text = '(no reply)';
  logEl.textContent += role + ":\\n" + text + "\\n\\n";
  logEl.scrollTop = logEl.scrollHeight;
}

function sendText() {
  var t = qEl.value.trim();
  if (!t) return;
  append('You', t);
  qEl.value = '';
  fetch('/ai_assistant/live_reply', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'q=' + encodeURIComponent(t)
  }).then(r => r.text()).then(txt => {
    if (txt && txt.indexOf('ERROR:') === 0) {
      append('Assistant', 'Error: ' + txt.substring(6).trim());
    } else {
      append('Assistant', txt || '(no reply)');
      speak(txt || '');
    }
  }).catch(e => append('Assistant', 'Error: ' + e));
}

// --- Speech: prevent the mic from hearing itself
var rec = null;
var speaking = false;

function detectLang(s) {
  // crude Arabic detection
  return /[\\u0600-\\u06FF]/.test(s) ? 'ar-LY' : 'en-US';
}
function startLive() {
  try {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { append('Assistant', 'Error: SpeechRecognition not supported in this browser.'); return; }
    rec = new SR();
    rec.continuous = true;
    rec.interimResults = false;
    // default language; we’ll adjust dynamically on results
    rec.lang = 'en-US';
    rec.onstart = function(){ micEl.textContent = 'Mic: listening...'; };
    rec.onerror = function(e){ append('Assistant', 'Error: mic ' + (e && e.error ? e.error : e)); };
    rec.onend = function(){ micEl.textContent = 'Mic: idle'; };
    rec.onresult = function(ev){
      var txt = '';
      for (var i = ev.resultIndex; i < ev.results.length; i++) {
        if (ev.results[i].isFinal) { txt += ev.results[i][0].transcript; }
      }
      txt = txt.trim();
      if (!txt) return;
      if (speaking) return; // ignore while assistant is speaking
      // set language for next chunk
      rec.lang = detectLang(txt);
      // send
      append('You', txt);
      fetch('/ai_assistant/live_reply', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'q=' + encodeURIComponent(txt)
      }).then(r => r.text()).then(ans => {
        if (ans && ans.indexOf('ERROR:') === 0) {
          append('Assistant', 'Error: ' + ans.substring(6).trim());
        } else {
          append('Assistant', ans || '(no reply)');
          speak(ans || '');
        }
      }).catch(e => append('Assistant', 'Error: ' + e));
    };
    rec.start();
  } catch(e) {
    append('Assistant', 'Error: could not start mic: ' + e);
  }
}
function stopLive(){ if (rec) try { rec.stop(); } catch(e){} micEl.textContent = 'Mic: idle'; }

function speak(text){
  if (!('speechSynthesis' in window)) return;
  if (!text) return;
  try {
    speaking = true;
    var u = new SpeechSynthesisUtterance(text);
    // choose voice language to match the text
    u.lang = detectLang(text);
    u.onend = function(){ speaking = false; };
    u.onerror = function(){ speaking = false; };
    window.speechSynthesis.speak(u);
  } catch(e) { speaking = false; }
}
</script>
</body>
</html>
"""

class LiveVoiceController(http.Controller):

    @http.route('/ai_assistant/live_chat', type='http', auth='user')
    def live_chat(self, **kw):
        return request.make_response(_HTML, headers=[('Content-Type', 'text/html; charset=utf-8')])

    @http.route('/ai_assistant/live_reply', type='http', auth='user', methods=['POST'], csrf=False)
    def live_reply(self, **kw):
        # Accept plain form field q
        q = (kw.get('q') or '').strip()
        if not q:
            return request.make_response('ERROR: empty question', [('Content-Type', 'text/plain; charset=utf-8')])
        text = _groq_chat_reply(q)
        # Always return text/plain so the frontend can print it directly
        return request.make_response(text, [('Content-Type', 'text/plain; charset=utf-8')])
