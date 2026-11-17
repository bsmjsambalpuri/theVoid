import json
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, expect

# --- CONFIGURATION ---
TARGET_URL = "https://your-website-url.com"  # <-- Replace with your actual URL
NEXT_BUTTON_SELECTOR = "#create-btn"
OUTPUT_FILE = "next_page_data.json"


def scrape_next_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        try:
            print(f"1. Opening {TARGET_URL}...")
            page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)

            # Bring page to front so JS countdown timers don't get throttled
            page.bring_to_front()

            # Locate the button (main page or iframe)
            button = page.locator(NEXT_BUTTON_SELECTOR)
            if button.count() == 0:
                for frame in page.frames:
                    if frame.locator(NEXT_BUTTON_SELECTOR).count() > 0:
                        button = frame.locator(NEXT_BUTTON_SELECTOR)
                        break

            print("2. Waiting for countdown to finish and button to unlock...")
            # Wait up to 20 seconds for the button to be visible AND enabled (not disabled)
            expect(button).to_be_visible(timeout=20000)
            expect(button).to_be_enabled(timeout=20000)

            # Extra 1.5s buffer after unlock to ensure JS event listeners are attached
            page.wait_for_timeout(1500)

            print(f"3. Clicking '{NEXT_BUTTON_SELECTOR}' (current value: {button.get_attribute('value')})...")
            initial_url = page.url

            # Normal click (without force=True) ensures the browser only clicks if truly interactive
            button.click()

            # Wait for either the URL to change OR the page content to reload
            try:
                page.wait_for_url(lambda url: url != initial_url, timeout=15000)
            except Exception:
                # If the URL stays the same (e.g. AJAX/SPA update), wait for network & DOM to settle
                page.wait_for_load_state("networkidle", timeout=15000)
                page.wait_for_timeout(3000)

            print(f"4. Loaded next page: {page.url}")

            page_text = page.locator("body").inner_text()

            extracted_data = {
                "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
                "next_page_url": page.url,
                "text_content": page_text.strip(),
            }

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)

            print(f"5. Success! Next page data saved to {OUTPUT_FILE}.")

        except Exception as e:
            print(f"ERROR occurred on URL: {page.url}")
            page.screenshot(path="debug_error.png", full_page=True)
            raise e
        finally:
            browser.close()


if __name__ == "__main__":
    scrape_next_page()