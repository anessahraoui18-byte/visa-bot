import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

TARGET_URL = "https://appointment.bmeia.gv.at/?fromSpecificInfo=True"
CHECK_INTERVAL = 120
RETRY_DELAY = 5
MAX_RETRIES = 3
STORAGE_STATE_FILE = "storage_state.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

AVAILABLE_MARKERS = [
    "available",
    "slots available",
    "freie termine",
    "appointments available",
]
NO_SLOTS_MARKERS = [
    "no slots available",
    "no appointments available",
    "keine freien termine",
    "currently no appointments",
]


def is_slot_available(page_text: str) -> bool:
    lower_text = page_text.lower()
    if any(marker in lower_text for marker in NO_SLOTS_MARKERS):
        return False
    return any(marker in lower_text for marker in AVAILABLE_MARKERS)


def apply_stealth(page):
    if stealth_sync:
        stealth_sync(page)
    page.add_init_script(
        "() => {"
        "Object.defineProperty(navigator, 'webdriver', {get: () => false});"
        "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});"
        "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});"
        "window.chrome = { runtime: {} };"
        "const originalQuery = window.navigator.permissions.query;"
        "window.navigator.permissions.query = parameters =>"
        "parameters.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : originalQuery(parameters);"
        "};"
    )


def create_browser_context(playwright):
    storage_state = STORAGE_STATE_FILE if Path(STORAGE_STATE_FILE).exists() else None
    return playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-infobars",
        ],
    ).new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        java_script_enabled=True,
        ignore_https_errors=True,
        timezone_id="Europe/Vienna",
        device_scale_factor=1,
        accept_downloads=False,
        storage_state=storage_state,
        extra_http_headers={
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-ua": '"Chromium";v="126", "Google Chrome";v="126", ";Not A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        },
    )


def retry_with_delay(action, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return action()
        except Exception as exc:
            last_exception = exc
            if attempt == max_retries:
                raise
            print(f"⚠️ Attempt {attempt} failed, retrying in {delay} seconds...: {exc}")
            time.sleep(delay)
    raise last_exception


def check_embassy_page(page, first_load=False) -> bool:
    def load_page():
        if first_load:
            page.goto(TARGET_URL, timeout=60000, wait_until="networkidle")
        else:
            page.reload(timeout=60000, wait_until="networkidle")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_selector("body", timeout=60000)
        body_text = page.inner_text("body")
        return is_slot_available(body_text)

    return retry_with_delay(load_page)


def main():
    print("🚀 Starting Austria embassy checker")

    with sync_playwright() as playwright:
        context = create_browser_context(playwright)
        page = context.new_page()
        apply_stealth(page)

        first_load = True
        while True:
            print("Checking Austria Embassy...")
            try:
                available = check_embassy_page(page, first_load=first_load)
                first_load = False
                context.storage_state(path=STORAGE_STATE_FILE)
                if available:
                    print("✅ Available slots detected on Austria Embassy page.")
                else:
                    print("❌ No available slots found.")
            except PlaywrightTimeoutError as exc:
                print(f"⚠️ Timeout loading page: {exc}")
            except Exception as exc:
                print(f"⚠️ Error checking page: {exc}")

            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
