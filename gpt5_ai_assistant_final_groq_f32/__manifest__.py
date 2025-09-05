{
    'name': 'GPT-5 Assistant (Groq, voice, chat history)',
    'version': '15.0.32.0',
    'summary': 'Simple AI assistant with Groq/OpenAI-compatible API, tool calls, voice I/O, and persistent history',
    'author': 'ChatGPT',
    'category': 'Tools',
    'depends': ['base', 'sale'],
    'data': [],
    'assets': {
        'web.assets_frontend': [
            '/gpt5_ai_assistant_final_groq_f32/static/src/js/recorder-worker.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}