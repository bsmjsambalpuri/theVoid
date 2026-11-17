import json
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
TARGET_URL = "https://freeiptv2023-d.ottc.xyz/"  # <-- Replace with your actual URL
NEXT_BUTTON_SELECTOR = "#create-btn"
OUTPUT_FILE = "next_page_data.json"


def scrape_next_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )

        # Hide navigator.webdriver so anti-bot JS timers don't freeze
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()

        try:
            print(f"1. Opening {TARGET_URL}...")
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            page.bring_to_front()

            # Simulate mouse movement & scroll to trigger timers that require user activity
            page.mouse.move(300, 300)
            page.mouse.wheel(0, 200)
            page.wait_for_timeout(1000)
            page.mouse.move(500, 400)

            print("2. Waiting for the countdown message to finish...")
            # Wait up to 30 seconds for "Please wait" text to disappear from the page
            try:
                page.get_by_text("Please wait", exact=False).wait_for(state="hidden", timeout=30000)
                print("   Countdown text disappeared!")
            except Exception:
                print("   Warning: 'Please wait' text still visible after 30s.")

            # Small buffer after countdown finishes
            page.wait_for_timeout(1500)

            # Check if #create-btn is enabled now
            button = page.locator(NEXT_BUTTON_SELECTOR)
            is_disabled = button.is_disabled()
            print(f"3. Button '{NEXT_BUTTON_SELECTOR}' -> disabled={is_disabled}, value={button.get_attribute('value')}")

            if is_disabled:
                # Debug: list all buttons/inputs on the page in case another button unlocked instead
                all_buttons = page.locator("button, input[type='submit'], input[type='button'], a.btn").all()
                print(f"   Found {len(all_buttons)} clickable elements on page:")
                for idx, btn in enumerate(all_buttons):
                    print(f"   [{idx}] id={btn.get_attribute('id')} value={btn.get_attribute('value')} text={btn.inner_text().strip()} disabled={btn.is_disabled()}")
                raise RuntimeError("Target button remained disabled after countdown.")

            initial_url = page.url
            print(f"4. Clicking '{NEXT_BUTTON_SELECTOR}'...")
            button.click()

            # Wait for navigation or DOM update
            try:
                page.wait_for_url(lambda url: url != initial_url, timeout=15000)
            except Exception:
                page.wait_for_load_state("networkidle", timeout=15000)
                page.wait_for_timeout(3000)

            print(f"5. Loaded next page: {page.url}")

            page_text = page.locator("body").inner_text()

            extracted_data = {
                "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
                "next_page_url": page.url,
                "text_content": page_text.strip(),
            }

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)

            print(f"6. Success! Next page data saved to {OUTPUT_FILE}.")

        except Exception as e:
            print(f"ERROR occurred on URL: {page.url}")
            page.screenshot(path="debug_error.png", full_page=True)
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            raise e
        finally:
            browser.close()


if __name__ == "__main__":
    scrape_next_page()