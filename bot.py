from pyrogram import Client, filters
from pyrogram.types import Message
import os

# قراءة المتغيرات
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found")
if not API_ID or not API_HASH:
    raise ValueError("❌ API_ID and API_HASH must be set")

app = Client("session_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# تخزين بيانات المستخدمين
user_data = {}

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "🤖 **بوت استخراج جلسات Pyrogram**\n\n"
        "📌 **الاستخدام:**\n"
        "1. أرسل `/session`\n"
        "2. أدخل API ID\n"
        "3. أدخل API HASH\n"
        "4. أدخل رقم الهاتف\n"
        "5. أدخل رمز التحقق\n\n"
        "⚠️ البوت لا يحفظ أي بيانات"
    )

@app.on_message(filters.command("session"))
async def start_session(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_data:
        if "temp_client" in user_data[user_id]:
            try:
                await user_data[user_id]["temp_client"].disconnect()
            except:
                pass
        del user_data[user_id]
    
    user_data[user_id] = {"step": "api_id"}
    await message.reply_text(
        "🔐 **الخطوة 1/4**\n\n"
        "أرسل **API ID** الخاص بك\n\n"
        "📍 من my.telegram.org"
    )

@app.on_message(filters.text & filters.private)
async def handle_input(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text.startswith('/'):
        return
    
    if user_id not in user_data:
        await message.reply_text("❌ أرسل `/session` أولاً")
        return
    
    step = user_data[user_id]["step"]
    
    if step == "api_id":
        try:
            api_id = int(text)
            user_data[user_id]["api_id"] = api_id
            user_data[user_id]["step"] = "api_hash"
            await message.reply_text("✅ **الخطوة 2/4**\n\nأرسل **API HASH**:")
        except:
            await message.reply_text("❌ API ID يجب أن يكون أرقاماً:\nأعد الإرسال:")
    
    elif step == "api_hash":
        user_data[user_id]["api_hash"] = text
        user_data[user_id]["step"] = "phone"
        await message.reply_text(
            "✅ **الخطوة 3/4**\n\n"
            "أرسل رقم هاتفك (بالصيغة الدولية)\n"
            "مثال: `+96170123456`"
        )
    
    elif step == "phone":
        if not text.startswith('+') or not text[1:].isdigit():
            await message.reply_text("❌ صيغة خاطئة!\nمثال: `+96170123456`\nأعد الإرسال:")
            return
        
        user_data[user_id]["phone"] = text
        user_data[user_id]["step"] = "waiting_code"
        await message.reply_text("🔄 جاري الاتصال...")
        
        try:
            temp_client = Client(
                f":memory:",
                api_id=user_data[user_id]["api_id"],
                api_hash=user_data[user_id]["api_hash"]
            )
            await temp_client.connect()
            sent_code = await temp_client.send_code(text)
            user_data[user_id]["temp_client"] = temp_client
            user_data[user_id]["phone_code_hash"] = sent_code.phone_code_hash
            await message.reply_text("📨 **الخطوة 4/4**\n\nأرسل رمز التحقق:")
        except Exception as e:
            await message.reply_text(f"❌ خطأ: {str(e)}\nأعد المحاولة بـ /session")
            if "temp_client" in user_data[user_id]:
                await user_data[user_id]["temp_client"].disconnect()
            del user_data[user_id]
    
    elif step == "waiting_code":
        if not text.isdigit():
            await message.reply_text("❌ الرمز يجب أن يكون أرقاماً:\nأعد الإرسال:")
            return
        
        try:
            temp_client = user_data[user_id]["temp_client"]
            await temp_client.sign_in(
                user_data[user_id]["phone"],
                text,
                user_data[user_id]["phone_code_hash"]
            )
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()
            
            await message.reply_text(
                f"✅ **تم استخراج الجلسة!**\n\n"
                f"`{session_string}`\n\n"
                f"⚠️ احفظها ولا تشاركها"
            )
            del user_data[user_id]
        except Exception as e:
            await message.reply_text(f"❌ خطأ: {str(e)}\nأعد المحاولة بـ /session")
            if "temp_client" in user_data[user_id]:
                await user_data[user_id]["temp_client"].disconnect()
            if user_id in user_data:
                del user_data[user_id]

if __name__ == "__main__":
    print("=" * 40)
    print("🤖 Bot is running as Worker")
    print("=" * 40)
    app.run()
