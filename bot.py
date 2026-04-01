import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

TARGET_URL = "https://appointment.bmeia.gv.at/?fromSpecificInfo=True"
CHECK_INTERVAL = 120

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


def check_embassy_page(page, first_load=False) -> bool:
    if first_load:
        page.goto(TARGET_URL, timeout=60000, wait_until="networkidle")
    else:
        page.reload(timeout=60000, wait_until="networkidle")

    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_selector("body", timeout=60000)
    body_text = page.inner_text("body")
    return is_slot_available(body_text)


def main():
    print("🚀 Starting Austria embassy checker")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            java_script_enabled=True,
            ignore_https_errors=True,
        )

        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => false});"
        )
        page.add_init_script(
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});"
        )
        page.add_init_script(
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});"
        )

        first_load = True
        while True:
            print("Checking Austria Embassy...")
            try:
                available = check_embassy_page(page, first_load=first_load)
                first_load = False
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
