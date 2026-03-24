import os
from pathlib import Path
from playwright.sync_api import sync_playwright

from backend.config import PROJECT_ROOT

WHATSAPP_SESSION_DIR = PROJECT_ROOT / "whatsapp_session"

def setup_whatsapp():
    """Run this function manually to scan the QR code the very first time."""
    print("Opening WhatsApp Web...")
    print("Please scan the QR code. Once your chats load, close the browser window.")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(WHATSAPP_SESSION_DIR),
            headless=False
        )
        page = browser.new_page()
        page.goto("https://web.whatsapp.com/")
        page.wait_for_timeout(60000) # Give 60 seconds to scan
        browser.close()

def send_whatsapp_message(target_name: str, message: str) -> str:
    """Headless message sending using the saved session data."""
    if not WHATSAPP_SESSION_DIR.exists():
        return "WhatsApp is not linked. Please run backend.actions.whatsapp_playwright setup first to scan your QR code."
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(WHATSAPP_SESSION_DIR),
                headless=True
            )
            page = browser.new_page()
            page.goto("https://web.whatsapp.com/")
            
            # Wait for search box to ensure loaded
            page.wait_for_selector('div[contenteditable="true"][@data-tab="3"]', timeout=30000)
            
            # Search for contact
            search_box = page.locator('div[contenteditable="true"][@data-tab="3"]')
            search_box.fill(target_name)
            page.wait_for_timeout(2000)
            
            # Press enter to open chat
            search_box.press("Enter")
            page.wait_for_timeout(2000)
            
            # Find the message input box and send
            msg_box = page.locator('div[contenteditable="true"][@data-tab="10"]')
            msg_box.fill(message)
            page.wait_for_timeout(500)
            msg_box.press("Enter")
            
            page.wait_for_timeout(2000)
            browser.close()
            return f"Silently sent a WhatsApp message to {target_name}"
            
    except Exception as e:
        return f"Failed to send WhatsApp message via automation: {e}"

if __name__ == "__main__":
    setup_whatsapp()
