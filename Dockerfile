FROM python:3.9-slim

WORKDIR /app

# تثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملف البوت
COPY bot.py .

# تشغيل البوت
CMD ["python", "bot.py"]
