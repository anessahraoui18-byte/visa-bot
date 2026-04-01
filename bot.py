import os
import requests
import time
from datetime import datetime

# إعدادات رادار السفارة النمساوية V3
API_URL = "https://appointment.bmeia.gv.at/?fromSpecificInfo=True"
CHECK_INTERVAL = 7  # يفحص كل 7 ثواني

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CATEGORIES = [
    {"name": "Bachelor", "query": "category=1", "label": "Category 1 (Bachelor)"},
    {"name": "Master", "query": "category=2", "label": "Category 2 (Master)"},
]

# الكلمات المفتاحية لتحديد حالة النتائج
NO_SLOTS_TEXT = ["No slots available", "لا توجد مواعيد متاحة"]
AVAILABLE_TEXT = ["Available", "متاحة"]

last_status = {category["name"]: None for category in CATEGORIES}


def get_category_url(category):
    return f"{API_URL}?{category['query']}"


def parse_slot_status(html_text):
    normalized = html_text.lower()
    if any(text.lower() in normalized for text in NO_SLOTS_TEXT):
        return "unavailable"
    if any(text.lower() in normalized for text in AVAILABLE_TEXT):
        return "available"
    return "unknown"


def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not configured. Skipping Telegram notification.")
        return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(telegram_url, data=payload, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ فشل إرسال إشعار تيليجرام: {response.status_code} - {response.text}")
    except Exception as exc:
        print(f"⚠️ حدث خطأ أثناء إرسال إشعار تيليجرام: {exc}")


def check_category(category):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}] 🔍 Checking Austria Embassy {category['name']}...")
    print(f"[{current_time}] 🎯 Simulating selection of {category['label']}...")

    try:
        response = requests.get(get_category_url(category), timeout=10)
        if response.status_code != 200:
            print(f"⚠️ {category['name']}: استجابة الموقع بكود {response.status_code}")
            return

        status = parse_slot_status(response.text)
        if status == "available":
            print(f"✅ {category['name']}: Available")
            if last_status[category["name"]] != "available":
                send_telegram_message(
                    f"🟢 <b>{category['label']}</b> slot is now available!"
                )
        elif status == "unavailable":
            print(f"❌ {category['name']}: No slots available")
        else:
            print(f"⚠️ {category['name']}: Unable to determine slot availability from page text")

        last_status[category["name"]] = status

    except Exception as exc:
        print(f"📡 {category['name']}: حدث خطأ أثناء الاتصال: {exc}")


if __name__ == "__main__":
    print("🚀 تم تشغيل رادار أنس V3")
    print("------------------------------------------")
    while True:
        for category in CATEGORIES:
            check_category(category)
        time.sleep(CHECK_INTERVAL)
