from pyrogram import Client, filters
from pyrogram.types import Message
import os

API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

app = Client("session_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# تخزين مؤقت لبيانات المستخدمين
user_data = {}

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "🤖 **بوت استخراج جلسات Pyrogram v2**\n\n"
        "أرسل `/session` لبدء استخراج جلسة جديدة\n\n"
        "⚠️ **تنبيه:** البوت لا يحفظ أي بيانات، الجلسة تظهر مرة واحدة فقط"
    )

@app.on_message(filters.command("session"))
async def start_session(client, message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "api_id"}
    await message.reply_text("📱 **الخطوة 1/3**\nأرسل API ID الخاص بك:")

@app.on_message(filters.text & filters.private)
async def handle_input(client, message: Message):
    user_id = message.from_user.id
    text = message.text
    
    if user_id not in user_data:
        return
    
    step = user_data[user_id]["step"]
    
    if step == "api_id":
        user_data[user_id]["api_id"] = int(text)
        user_data[user_id]["step"] = "api_hash"
        await message.reply_text("🔑 **الخطوة 2/3**\nأرسل API HASH الخاص بك:")
    
    elif step == "api_hash":
        user_data[user_id]["api_hash"] = text
        user_data[user_id]["step"] = "phone"
        await message.reply_text("📞 **الخطوة 3/3**\nأرسل رقم هاتفك (بالصيغة الدولية):\nمثال: +96170000000")
    
    elif step == "phone":
        api_id = user_data[user_id]["api_id"]
        api_hash = user_data[user_id]["api_hash"]
        phone = text
        
        await message.reply_text("🔄 جاري الاتصال بحسابك...")
        
        try:
            # إنشاء جلسة مؤقتة
            async with Client(":memory:", api_id=api_id, api_hash=api_hash) as temp_client:
                # إرسال رمز التحقق
                sent_code = await temp_client.send_code(phone)
                user_data[user_id]["phone"] = phone
                user_data[user_id]["phone_code_hash"] = sent_code.phone_code_hash
                user_data[user_id]["step"] = "code"
                await message.reply_text("📨 تم إرسال رمز التحقق إلى تليجرام\nأرسل الرمز هنا:")
                
        except Exception as e:
            await message.reply_text(f"❌ خطأ: {str(e)}")
            del user_data[user_id]
    
    elif step == "code":
        code = text
        api_id = user_data[user_id]["api_id"]
        api_hash = user_data[user_id]["api_hash"]
        phone = user_data[user_id]["phone"]
        phone_code_hash = user_data[user_id]["phone_code_hash"]
        
        try:
            async with Client(":memory:", api_id=api_id, api_hash=api_hash) as temp_client:
                await temp_client.sign_in(phone, code, phone_code_hash)
                session_string = await temp_client.export_session_string()
                
                await message.reply_text(
                    f"✅ **تم استخراج الجلسة بنجاح!**\n\n"
                    f"```\n{session_string}\n```\n\n"
                    f"⚠️ **حافظ على هذا النص آمناً ولا تشاركه مع أي شخص!**"
                )
                del user_data[user_id]
                
        except Exception as e:
            await message.reply_text(f"❌ خطأ: {str(e)}")
            del user_data[user_id]

app.run()
