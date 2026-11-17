import json
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
TARGET_URL = "https://your-website-url.com"  # <-- Replace with your actual URL
NEXT_BUTTON_SELECTOR = "#create-btn"         # Targets <input id="create-btn" ...>
WAIT_SECONDS = 6
OUTPUT_FILE = "next_page_data.json"


def scrape_next_page():
    with sync_playwright() as p:
        # Must be headless=True when running on GitHub Actions
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"1. Opening {TARGET_URL}...")
        page.goto(TARGET_URL, wait_until="domcontentloaded")

        print(f"2. Waiting for {WAIT_SECONDS} seconds...")
        page.wait_for_timeout(WAIT_SECONDS * 1000)

        print(f"3. Clicking '{NEXT_BUTTON_SELECTOR}'...")
        page.locator(NEXT_BUTTON_SELECTOR).click()

        # Wait for the next page to finish loading after click
        page.wait_for_load_state("networkidle")
        print(f"4. Loaded next page: {page.url}")

        # Extract visible text from the next page
        page_text = page.locator("body").inner_text()

        extracted_data = {
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "next_page_url": page.url,
            "text_content": page_text.strip(),
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)

        print(f"5. Success! Next page data saved to {OUTPUT_FILE}.")
        browser.close()


if __name__ == "__main__":
    scrape_next_page()