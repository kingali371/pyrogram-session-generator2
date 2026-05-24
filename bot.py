from pyrogram import Client, filters
from pyrogram.types import Message
import os
import asyncio

# قراءة توكن البوت من متغيرات البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على BOT_TOKEN في متغيرات البيئة")

# إنشاء البوت
app = Client(
    "session_bot",
    bot_token=BOT_TOKEN,
    api_id=6,  # رقم وهمي، سيتم استبداله ببيانات المستخدم
    api_hash="dummy"  # قيمة وهمية، سيتم استبداله ببيانات المستخدم
)

# تخزين مؤقت لبيانات المستخدمين
user_data = {}

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "🤖 **بوت استخراج جلسات Pyrogram v2**\n\n"
        "هذا البوت يساعدك لاستخراج جلسة Pyrogram الخاصة بك\n"
        "📍 **المميزات:**\n"
        "• يستخدم بيانات API الخاصة بك (وليس بيانات البوت)\n"
        "• لا يتم حفظ أي بيانات بعد انتهاء الجلسة\n"
        "• آمن وموثوق\n\n"
        "أرسل `/session` لبدء استخراج جلسة جديدة\n\n"
        "⚠️ **تحذير:** لا تشارك نص الجلسة مع أي شخص!"
    )

@app.on_message(filters.command("session"))
async def start_session(client, message: Message):
    user_id = message.from_user.id
    
    # تنظيف أي بيانات سابقة للمستخدم
    if user_id in user_data:
        if "temp_client" in user_data[user_id]:
            try:
                await user_data[user_id]["temp_client"].disconnect()
            except:
                pass
        del user_data[user_id]
    
    user_data[user_id] = {"step": "api_id"}
    await message.reply_text(
        "🔐 **الخطوة 1 من 4**\n\n"
        "أرسل **API ID** الخاص بك\n\n"
        "📍 **كيف تحصل على API ID و API HASH؟**\n"
        "1. اذهب إلى https://my.telegram.org\n"
        "2. سجل الدخول بحسابك\n"
        "3. اذهب إلى 'API Development Tools'\n"
        "4. انسخ الـ `api_id` و `api_hash`\n\n"
        "📝 **مثال:** `12345678`"
    )

@app.on_message(filters.text & filters.private)
async def handle_input(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # تجاهل الأوامر
    if text.startswith('/'):
        return
    
    # إذا لم يبدأ المستخدم العملية
    if user_id not in user_data:
        await message.reply_text("❌ أرسل `/session` أولاً لبدء استخراج الجلسة")
        return
    
    step = user_data[user_id]["step"]
    
    # ========== الخطوة 1: استقبال API ID ==========
    if step == "api_id":
        try:
            api_id = int(text)
            if api_id <= 0:
                raise ValueError
            user_data[user_id]["api_id"] = api_id
            user_data[user_id]["step"] = "api_hash"
            await message.reply_text(
                "✅ **تم استلام API ID**\n\n"
                "🔑 **الخطوة 2 من 4**\n\n"
                "أرسل **API HASH** الخاص بك الآن\n\n"
                "📝 **مثال:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`"
            )
        except ValueError:
            await message.reply_text("❌ **خطأ:** API ID يجب أن يكون أرقاماً فقط!\n\nأعد إرسال API ID:")
    
    # ========== الخطوة 2: استقبال API HASH ==========
    elif step == "api_hash":
        if len(text) < 10:
            await message.reply_text("❌ **خطأ:** API HASH قصير جداً! تأكد من نسخه بشكل صحيح\n\nأعد إرسال API HASH:")
            return
        
        user_data[user_id]["api_hash"] = text
        user_data[user_id]["step"] = "phone"
        await message.reply_text(
            "✅ **تم استلام API HASH**\n\n"
            "📞 **الخطوة 3 من 4**\n\n"
            "أرسل رقم هاتفك **بالصيغة الدولية**\n\n"
            "📝 **أمثلة:**\n"
            "• لبنان: `+96170123456`\n"
            "• مصر: `+201012345678`\n"
            "• السعودية: `+966512345678`\n"
            "• الإمارات: `+971501234567`"
        )
    
    # ========== الخطوة 3: استقبال رقم الهاتف وإرسال رمز التحقق ==========
    elif step == "phone":
        phone = text
        
        # التحقق من صيغة رقم الهاتف
        if not phone.startswith('+') or not phone[1:].isdigit():
            await message.reply_text(
                "❌ **خطأ في صيغة رقم الهاتف!**\n\n"
                "يجب أن يبدأ بعلامة `+` متبوعة بالأرقام فقط\n\n"
                "📝 **مثال صحيح:** `+96170123456`\n\n"
                "أعد إرسال رقم الهاتف:"
            )
            return
        
        user_data[user_id]["phone"] = phone
        user_data[user_id]["step"] = "waiting_code"
        
        await message.reply_text("🔄 **جاري الاتصال بتليجرام...**\n\n⏳ يرجى الانتظار...")
        
        try:
            # إنشاء عميل مؤقت ببيانات المستخدم
            temp_client = Client(
                f":memory:{user_id}",
                api_id=user_data[user_id]["api_id"],
                api_hash=user_data[user_id]["api_hash"]
            )
            
            await temp_client.connect()
            
            # إرسال رمز التحقق
            sent_code = await temp_client.send_code(phone)
            
            # حفظ بيانات الجلسة
            user_data[user_id]["temp_client"] = temp_client
            user_data[user_id]["phone_code_hash"] = sent_code.phone_code_hash
            
            await message.reply_text(
                "📨 **تم إرسال رمز التحقق!**\n\n"
                "**الخطوة 4 من 4 (الأخيرة)**\n\n"
                "الرجاء إرسال رمز التحقق الذي وصل إلى تطبيق تليجرام:\n\n"
                "⚠️ الرمز مكون من 5 أرقام عادة\n"
                "⏳ صلاحية الرمز: دقيقتان"
            )
            
        except Exception as e:
            error_msg = str(e)
            if "PHONE_NUMBER_INVALID" in error_msg:
                await message.reply_text("❌ **رقم الهاتف غير صحيح!**\n\nتأكد من:\n• كتابة الرقم بالصيغة الدولية\n• وجود الرقم في تليجرام\n\nأعد إرسال الرقم:")
            elif "FLOOD_WAIT" in error_msg:
                await message.reply_text("⚠️ **الطلب مكرر!**\n\nانتظر دقيقة ثم حاول مرة أخرى عن طريق `/session`")
            else:
                await message.reply_text(f"❌ **حدث خطأ:**\n`{error_msg}`\n\nأعد المحاولة بـ `/session`")
            
            # تنظيف البيانات
            if "temp_client" in user_data[user_id]:
                try:
                    await user_data[user_id]["temp_client"].disconnect()
                except:
                    pass
            del user_data[user_id]
    
    # ========== الخطوة 4: التحقق من الرمز واستخراج الجلسة ==========
    elif step == "waiting_code":
        code = text
        
        # التحقق من أن الرمز أرقام فقط
        if not code.isdigit():
            await message.reply_text("❌ **رمز التحقق يجب أن يكون أرقاماً فقط!**\n\nأعد إرسال الرمز:")
            return
        
        await message.reply_text("✅ **جاري التحقق من الرمز...**\n\n🔄 يرجى الانتظار...")
        
        try:
            temp_client = user_data[user_id]["temp_client"]
            phone = user_data[user_id]["phone"]
            phone_code_hash = user_data[user_id]["phone_code_hash"]
            
            # تسجيل الدخول بالرمز
            await temp_client.sign_in(phone, code, phone_code_hash)
            
            # استخراج نص الجلسة
            session_string = await temp_client.export_session_string()
            
            # إغلاق الاتصال
            await temp_client.disconnect()
            
            # إرسال الجلسة للمستخدم
            await message.reply_text(
                "✅ **تم استخراج الجلسة بنجاح!**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📋 **نص الجلسة (Session String):**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"`{session_string}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ **تحذير أمني مهم جداً:**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "• هذا النص يعادل **كلمة مرور حسابك**\n"
                "• **لا تشاركه** مع أي شخص أبداً\n"
                "• من يمتلكه يستطيع التحكم بحسابك بالكامل\n"
                "• احفظه في مكان آمن جداً\n\n"
                "🔒 **تم حذف جميع بياناتك المؤقتة من خوادم البوت**\n\n"
                "🔄 لإعادة الاستخراج، أرسل `/session` مرة أخرى"
            )
            
            # تنظيف البيانات
            del user_data[user_id]
            
        except Exception as e:
            error_msg = str(e)
            if "PHONE_CODE_INVALID" in error_msg:
                await message.reply_text("❌ **رمز التحقق غير صحيح!**\n\nتأكد من:\n• كتابة الرقم بشكل صحيح\n• عدم انتهاء صلاحية الرمز\n\nأعد إرسال الرمز:")
            elif "PHONE_CODE_EXPIRED" in error_msg:
                await message.reply_text("❌ **انتهت صلاحية الرمز!**\n\nأعد المحاولة بـ `/session`")
            else:
                await message.reply_text(f"❌ **حدث خطأ:**\n`{error_msg}`\n\nأعد المحاولة بـ `/session`")
            
            # تنظيف البيانات
            if "temp_client" in user_data[user_id]:
                try:
                    await user_data[user_id]["temp_client"].disconnect()
                except:
                    pass
            if user_id in user_data:
                del user_data[user_id]

# تشغيل البوت
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 بوت استخراج جلسات Pyrogram v2")
    print("=" * 50)
    print(f"✅ البوت يعمل الآن...")
    print("⚠️ تأكد من إضافة BOT_TOKEN في متغيرات البيئة")
    print("=" * 50)
    app.run()
