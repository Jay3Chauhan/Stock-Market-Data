#!/usr/bin/env python3
"""
NSE Cookie Generator - Run on Local Machine
============================================
This script generates NSE cookies on your local Windows/Mac machine
and outputs them to a file that can be uploaded to the low-memory VM.

Usage:
    python generate_cookies_local.py

Then upload nse_cookies.json to your VM:
    scp nse_cookies.json ubuntu@<VM_IP>:~/Stock-Market-Data/
"""

import os
import sys
import json
import time
import random
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("ERROR: selenium and undetected-chromedriver required")
    print("Run: pip install selenium undetected-chromedriver")
    sys.exit(1)

# NSE URLs for cookie rotation
NSE_COOKIE_ROTATION_URLS = [
    "https://www.nseindia.com/",
    "https://www.nseindia.com/get-quotes/equity?symbol=RELIANCE",
    "https://www.nseindia.com/market-data/live-equity-market",
]

# Required NSE cookies
REQUIRED_NSE_COOKIES = [
    'nsit', 'nseappid', 'ak_bmsc', 'AKA_A2', 'bm_mi', 
    'bm_sv', 'bm_sz', '_abck', 'RT', '_ga'
]

def get_chrome_driver():
    """Launch Chrome with anti-detection settings"""
    print("🚀 Launching Chrome browser...")
    
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36")
    
    return uc.Chrome(options=options, use_subprocess=True)

def generate_nse_cookies():
    """Generate fresh NSE cookies"""
    driver = None
    try:
        target_url = random.choice(NSE_COOKIE_ROTATION_URLS)
        print(f"📡 Fetching cookies from: {target_url}")
        
        driver = get_chrome_driver()
        driver.get(target_url)
        
        # Wait for page load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            pass
        
        time.sleep(5)  # Extra wait for cookies to be set
        
        cookies = driver.get_cookies()
        
        if not cookies:
            print("❌ No cookies received!")
            return None
        
        # Filter for required cookies
        filtered = {c['name']: c['value'] for c in cookies if c['name'] in REQUIRED_NSE_COOKIES}
        
        # Show which cookies we got
        print(f"\n✅ Received {len(filtered)} cookies:")
        for name in filtered:
            print(f"   • {name}")
        
        missing = [name for name in REQUIRED_NSE_COOKIES if name not in filtered]
        if missing:
            print(f"\n⚠️  Missing cookies (usually optional): {missing}")
        
        return filtered
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def save_cookies(cookies, output_file="nse_cookies.json"):
    """Save cookies to JSON file with extended expiry for VM use"""
    # Set expiry to 6 hours (for VM use)
    data = {
        "cookies": cookies,
        "timestamp": datetime.now().isoformat(),
        "expiry": time.time() + (6 * 3600),  # 6 hours
        "generated_on": "local_machine",
        "note": "Upload this file to your VM"
    }
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n💾 Cookies saved to: {output_file}")
    return output_file

def main():
    print("=" * 50)
    print("   NSE Cookie Generator for VM Deployment")
    print("=" * 50)
    print()
    
    cookies = generate_nse_cookies()
    
    if cookies:
        output_file = save_cookies(cookies)
        
        print()
        print("=" * 50)
        print("   ✅ SUCCESS!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("1. Upload to your VM:")
        print(f"   scp {output_file} ubuntu@<VM_IP>:~/Stock-Market-Data/")
        print()
        print("2. Restart the container:")
        print("   docker-compose -f docker-compose.lite.yml restart")
        print()
        print("⏰ Cookies will expire in 6 hours. Re-run this script to refresh.")
        print()
    else:
        print()
        print("❌ Failed to generate cookies. Try again or check your network.")
        sys.exit(1)

if __name__ == "__main__":
    main()
