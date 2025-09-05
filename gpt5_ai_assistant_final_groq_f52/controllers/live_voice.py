# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class AiAssistantLiveVoiceController(http.Controller):
    """
    Drop-in replacement for controllers/live_voice.py
    - Avoids f-strings in HTML template (prevents SyntaxError on some builds)
    - Better error reporting to the browser
    - Safer Groq/OpenAI-compatible call with robust parsing
    - Live mic loop-guard to stop self-echo
    """
    @staticmethod
    def _get_cfg():
        ICP = request.env['ir.config_parameter'].sudo()
        base_url = ICP.get_param('ai_assistant.base_url', default='https://api.groq.com/openai/v1') or 'https://api.groq.com/openai/v1'
        api_key = ICP.get_param('ai_assistant.api_key', default='') or ''
        model = ICP.get_param('ai_assistant.model', default='llama-3.1-8b-instant') or 'llama-3.1-8b-instant'
        system = ICP.get_param('ai_assistant.system', default='You are a helpful Odoo assistant. Keep replies concise.') or 'You are a helpful Odoo assistant. Keep replies concise.'
        return {'base_url': base_url, 'api_key': api_key, 'model': model, 'system': system}

    @staticmethod
    def _chat_complete(messages):
        import requests, json
        cfg = AiAssistantLiveVoiceController._get_cfg()
        if not cfg['api_key']:
            return False, 'API key missing. Set it in Settings → Technical → System Parameters (ai_assistant.api_key).'

        url = cfg['base_url'].rstrip('/') + '/chat/completions'
        headers = {
            'Authorization': 'Bearer ' + cfg['api_key'],
            'Content-Type': 'application/json'
        }
        payload = {
            'model': cfg['model'],
            'messages': messages,
            'temperature': 0.6,
        }
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        except Exception as e:
            return False, 'HTTP error: {}'.format(e)

        if resp.status_code != 200:
            try:
                data = resp.json()
                msg = data.get('error', {}).get('message') or data
            except Exception:
                msg = resp.text
            return False, 'API error ({}): {}'.format(resp.status_code, msg)

        try:
            data = resp.json()
            choices = data.get('choices') or []
            text = None
            if choices:
                text = (((choices[0] or {}).get('message') or {}).get('content'))
                if not text:
                    text = (choices[0] or {}).get('text')
            if not text:
                return False, 'Empty response from model.'
            return True, str(text)
        except Exception as e:
            return False, 'Parse error: {}'.format(e)

    @http.route('/ai_assistant/live_chat', type='http', auth='user', csrf=False)
    def live_chat(self, **kw):
        cfg = self._get_cfg()
        warn = '' if cfg['api_key'] else "<p style='color:red'>⚠️ No API key configured. Set ai_assistant.api_key to use Groq/OpenAI-compatible API.</p>"
        tpl = []
        tpl.append('<!doctype html>')
        tpl.append('<html>')
        tpl.append('<head>')
        tpl.append("<meta charset=\'utf-8\' />")
        tpl.append('<title>Live Voice Chat</title>')
        tpl.append('<meta name="viewport" content="width=device-width,initial-scale=1" />')
        tpl.append('</head>')
        tpl.append('<body>')
        tpl.append('<h2>Live Voice Chat</h2>')
        tpl.append(warn)
        tpl.append("<div id=\'mic\'>Mic: <span id=\'mic_state\'>idle</span></div>")
        tpl.append("<div id=\'log\' style=\'white-space:pre-wrap;border:1px solid #ccc;padding:8px;height:60vh;overflow:auto;margin:8px 0\'></div>")
        tpl.append("<textarea id=\'q\' placeholder=\'Type or speak...\' style=\'width:70%\'></textarea>")
        tpl.append("<button id=\'send\'>Send</button>")
        tpl.append("<button id=\'live\'>Live</button>")
        tpl.append("<button id=\'stop\'>Stop</button>")
        tpl.append('<script>')
        tpl.append('(function(){')
        tpl.append("const log=document.getElementById(\'log\');const micSpan=document.getElementById(\'mic_state\');const q=document.getElementById(\'q\');const btnSend=document.getElementById(\'send\');const btnLive=document.getElementById(\'live\');const btnStop=document.getElementById(\'stop\');")
        tpl.append("function append(role,text){log.textContent+=role+':\\n'+(text||'(no reply)')+'\\n\\n';log.scrollTop=log.scrollHeight;}")
        tpl.append('// TTS')
        tpl.append('let speaking=false;')
        tpl.append('function speak(text){try{speaking=true;if(\'speechSynthesis\' in window){const u=new SpeechSynthesisUtterance(text);if(/[\\u0600-\\u06FF]/.test(text))u.lang=\'ar-SA\';else u.lang=\'en-US\';u.onend=()=>{speaking=false;};window.speechSynthesis.cancel();window.speechSynthesis.speak(u);}else{speaking=false;}}catch(e){speaking=false;}}')
        tpl.append('async function send(text){if(!text)return;append("You",text);q.value="";try{const form=new URLSearchParams();form.set("q",text);const r=await fetch("/ai_assistant/send",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:form});const ct=(r.headers.get("content-type")||"").toLowerCase();let payload=await r.text();let out=payload;try{if(ct.includes("application/json")){const j=JSON.parse(payload);out=j.ok?j.text:("Error: "+(j.error||"unknown"));}}catch(e){}append("Assistant",out);if(!out.startsWith("Error: "))speak(out);}catch(e){append("Assistant","Error: "+e);}}')
        tpl.append('document.getElementById("send").onclick=()=>send(q.value);')
        tpl.append('// Speech Recognition')
        tpl.append('let recog;let stopReq=false;')
        tpl.append('function startLive(){if(!(\'webkitSpeechRecognition\' in window||\'SpeechRecognition\' in window)){append("System","Browser speech recognition not available.");return;}const SR=window.SpeechRecognition||window.webkitSpeechRecognition;recog=new SR();recog.lang="en-US";recog.continuous=true;recog.interimResults=false;recog.onstart=()=>micSpan.textContent="listening...";recog.onend=()=>{if(!stopReq)try{recog.start();}catch(e){}};recog.onerror=(ev)=>{micSpan.textContent="error";append("System","Mic error: "+(ev&&ev.error?ev.error:"unknown"));};recog.onresult=(ev)=>{if(speaking)return;const last=ev.results[ev.results.length-1];const text=(last&&last[0]&&last[0].transcript?last[0].transcript.trim():"");if(!text)return;if(/[\\u0600-\\u06FF]/.test(text))recog.lang="ar-SA";else recog.lang="en-US";send(text);};stopReq=false;try{recog.start();}catch(e){append("System","Failed to start mic: "+e);} }')
        tpl.append('function stopLive(){stopReq=true;if(recog)try{recog.stop();}catch(e){}micSpan.textContent="idle";}')
        tpl.append('document.getElementById("live").onclick=startLive;document.getElementById("stop").onclick=stopLive;')
        tpl.append('})();')
        tpl.append('</script>')
        tpl.append('</body>')
        tpl.append('</html>')
        return '\n'.join(tpl)

    @http.route('/ai_assistant/send', type='http', auth='user', csrf=False, methods=['POST'])
    def send(self, **post):
        import json as _json
        q = (post.get('q') or '').strip()
        if not q:
            payload = {'ok': False, 'error': 'Empty input.'}
            return request.make_response(_json.dumps(payload), headers=[('Content-Type','application/json; charset=utf-8')])
        cfg = self._get_cfg()
        messages = [
            {'role':'system','content': cfg['system']},
            {'role':'user','content': q},
        ]
        ok, out = self._chat_complete(messages)
        if ok:
            payload = {'ok': True, 'text': out}
        else:
            payload = {'ok': False, 'error': out}
        return request.make_response(_json.dumps(payload), headers=[('Content-Type','application/json; charset=utf-8')])