import json
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
TARGET_URL = "https://freeiptv2023-d.ottc.xyz/"  # <-- Replace with your actual URL
NEXT_BUTTON_SELECTOR = "#create-btn"
WAIT_SECONDS = 10
OUTPUT_FILE = "next_page_data.json"


def scrape_next_page():
    with sync_playwright() as p:
        # Launch with flags that reduce headless bot detection
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Use a standard Windows Chrome User-Agent and viewport
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        try:
            print(f"1. Opening {TARGET_URL}...")
            page.goto(TARGET_URL, wait_until="load", timeout=60000)

            print(f"2. Waiting for {WAIT_SECONDS} seconds...")
            page.wait_for_timeout(WAIT_SECONDS * 1000)

            # Check main page first; if not found, search inside any iframes
            button = page.locator(NEXT_BUTTON_SELECTOR)
            if button.count() == 0:
                print("Button not on main page, checking iframes...")
                for frame in page.frames:
                    if frame.locator(NEXT_BUTTON_SELECTOR).count() > 0:
                        button = frame.locator(NEXT_BUTTON_SELECTOR)
                        print("Found button inside an iframe!")
                        break

            # Wait up to 15s for the button to become visible & enabled
            button.wait_for(state="visible", timeout=15000)
            
            print(f"3. Clicking '{NEXT_BUTTON_SELECTOR}'...")
            button.click(force=True)

            # Wait for the next page to finish loading
            page.wait_for_load_state("networkidle", timeout=30000)
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
            print(f"Page title was: {page.title()}")
            # Save screenshot & HTML so you can inspect why the button wasn't found
            page.screenshot(path="debug_error.png", full_page=True)
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            raise e
        finally:
            browser.close()


if __name__ == "__main__":
    scrape_next_page()