import requests
import time
from datetime import datetime

# إعدادات الرادار V3
API_URL = "https://الرابط-الخاص-بموقع-الفيزا"  # ضع هنا رابط الموقع الفعلي
CHECK_INTERVAL = 7  # يفحص كل 7 ثواني


def check_visa_slots():
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}] 🔍 جاري فحص المواعيد في موقع VFS Global...")

    try:
        response = requests.get(API_URL, timeout=10)

        if response.status_code == 200:
            print("✅ الموقع شغال.. لا توجد مواعيد متاحة حالياً.")
        else:
            print(f"⚠️ تنبيه: الموقع استجاب بكود {response.status_code}")

    except Exception as exc:
        print(f"📡 حدث خطأ أثناء الاتصال: {exc}")
        print("📡 نبض السيرفر شغال.. في انتظار الاستجابة في المحاولة التالية...")


if __name__ == "__main__":
    print("🚀 تم تشغيل رادار أنس V3")
    print("------------------------------------------")
    while True:
        check_visa_slots()
        time.sleep(CHECK_INTERVAL)
