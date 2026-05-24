from pyrogram import Client
from flask import Flask, request, jsonify, render_template_string
import os
import asyncio

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>مولد جلسات Pyrogram</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            direction: rtl;
        }
        .container {
            max-width: 500px;
            margin: 50px auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        input, button {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: scale(1.02); }
        .result {
            margin-top: 20px;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 8px;
            display: none;
            word-break: break-all;
        }
        .result pre {
            white-space: pre-wrap;
            background: #2d2d2d;
            color: #4ec9b0;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 10px;
            border-radius: 8px;
            display: none;
            margin-top: 10px;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 مولد جلسات Pyrogram v2</h1>
        <form id="sessionForm">
            <input type="text" id="api_id" placeholder="API ID" required>
            <input type="text" id="api_hash" placeholder="API HASH" required>
            <input type="text" id="phone" placeholder="رقم الهاتف (مثال: +961xxxxxxxx)" required>
            <input type="password" id="password" placeholder="كلمة مرور الخطوتين (اختياري)">
            <button type="submit">🚀 استخراج الجلسة</button>
        </form>
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>جاري الاتصال بحساب تليجرام...</p>
        </div>
        <div class="result" id="result">
            <strong>✅ نص الجلسة الخاص بك:</strong>
            <pre id="sessionString"></pre>
            <button onclick="copySession()">📋 نسخ</button>
        </div>
        <div class="error" id="error"></div>
    </div>
    <script>
        function copySession() {
            const sessionText = document.getElementById('sessionString').innerText;
            navigator.clipboard.writeText(sessionText);
            alert('تم نسخ الجلسة!');
        }
        
        document.getElementById('sessionForm').onsubmit = async (e) => {
            e.preventDefault();
            
            const api_id = document.getElementById('api_id').value;
            const api_hash = document.getElementById('api_hash').value;
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({api_id, api_hash, phone, password})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('sessionString').innerText = data.session;
                    document.getElementById('result').style.display = 'block';
                } else {
                    document.getElementById('error').innerText = '❌ ' + data.error;
                    document.getElementById('error').style.display = 'block';
                }
            } catch (err) {
                document.getElementById('error').innerText = 'خطأ في الاتصال: ' + err.message;
                document.getElementById('error').style.display = 'block';
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        api_id = int(data.get('api_id'))
        api_hash = data.get('api_hash')
        phone = data.get('phone')
        password = data.get('password') or None
        
        # استخراج الجلسة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def create_session():
            try:
                client = Client(":memory:", api_id=api_id, api_hash=api_hash)
                await client.connect()
                
                # إرسال رمز التحقق
                sent_code = await client.send_code(phone)
                
                # في Render، نحتاج طريقة مختلفة للحصول على الكود
                # الحل: استخدام webhook أو انتظار إدخال المستخدم
                # لكن هذا معقد، لذا سنستخدم طريقة بديلة
                
                await client.disconnect()
                return None, "يجب استخدام نسخة CLI لهذه الطريقة. يرجى استخدام التطبيق المحلي."
                
            except Exception as e:
                return None, str(e)
        
        result, error = loop.run_until_complete(create_session())
        loop.close()
        
        if error:
            return jsonify({'success': False, 'error': error})
        return jsonify({'success': True, 'session': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
