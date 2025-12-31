import os
import json
import time
import random
from datetime import datetime
from typing import Dict, Optional

import requests

# Make Selenium/Chrome optional for low-memory VMs
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
    uc.Chrome.__del__ = lambda self: None
except ImportError:
    uc = None
    SELENIUM_AVAILABLE = False

from Utils.logger import get_logger
from Utils.config_reader import configure
from Constant.general import NSE_GET_COOKIES_HEADERS, REQUIRED_NSE_COOKIES, NSE_COOKIE_ROTATION_URLS
    
logger = get_logger(__name__)


class NSECookieService:
    """
    NSE Cookie Service - Fetches and manages cookies for NSE API access.
    
    Supports two modes:
    1. HTTP-based (works on low-memory VMs without Chrome)
    2. Selenium-based (for full cookie extraction when HTTP fails)
    """
    
    def __init__(self):
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.cookies_file = configure.get('NSE', 'COOKIES_FILE')
        self.session = requests.Session()
        # Set default headers for session
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })

    def get_cookies_via_http(self) -> Optional[Dict[str, str]]:
        """
        Get NSE cookies using HTTP requests (no Selenium needed).
        This method works on low-memory VMs without Chrome.
        """
        try:
            # Create a fresh session for each attempt
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Step 1: Visit the main NSE page to get initial cookies
            logger.info("Fetching cookies via HTTP requests...")
            target_url = random.choice(NSE_COOKIE_ROTATION_URLS)
            logger.info(f"Visiting: {target_url}")
            
            response = session.get(target_url, timeout=30, allow_redirects=True)
            
            if response.status_code != 200:
                logger.warning(f"Initial request returned status {response.status_code}")
            
            # Step 2: Make a request to an API endpoint to ensure cookies are set
            time.sleep(1)  # Small delay
            api_url = f"{self.base_url}/api/allIndices"
            api_response = session.get(api_url, timeout=30)
            
            # Collect cookies from session
            cookies = dict(session.cookies)
            
            if not cookies:
                logger.warning("No cookies received from HTTP request")
                return None
            
            logger.info(f"Received {len(cookies)} cookies via HTTP")
            logger.debug(f"Cookies: {list(cookies.keys())}")
            
            # Check if we got essential cookies
            essential_cookies = ['nsit', 'nseappid', 'bm_sv', 'bm_sz']
            has_essential = any(c in cookies for c in essential_cookies)
            
            if has_essential:
                logger.info("Successfully obtained essential NSE cookies via HTTP")
                self._save_cookies_to_file(cookies)
                return cookies
            else:
                logger.warning("HTTP cookies may be incomplete, but attempting to use them")
                self._save_cookies_to_file(cookies)
                return cookies
                
        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching cookies via HTTP")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error while fetching cookies: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching cookies via HTTP: {e}")
            return None

    def get_driver(self):
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium/Chrome not available on this system")
            return None
            
        logger.info("Launching undetected Chrome...")

        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/143.0.0.0 Safari/537.36")

        return uc.Chrome(options=options, use_subprocess=True)

    def get_cookies_via_selenium(self) -> Optional[Dict[str, str]]:
        """Get cookies using Selenium (fallback when HTTP doesn't work)."""
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available")
            return None
            
        try:
            target_url = random.choice(NSE_COOKIE_ROTATION_URLS)
            logger.info(f"Getting cookies via Selenium: {target_url}")

            driver = self.get_driver()
            if not driver:
                return None
                
            driver.get(target_url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except Exception as e:
                logger.warning(f"Page load wait failed: {e}")

            time.sleep(3)

            cookies = driver.get_cookies()
            driver.quit()

            if not cookies:
                logger.warning("No cookies received from Selenium")
                return None

            filtered = {c['name']: c['value'] for c in cookies if c['name'] in REQUIRED_NSE_COOKIES}
            missing = [name for name in REQUIRED_NSE_COOKIES if name not in filtered]
            if missing:
                logger.warning(f"Missing cookies: {missing}")
            else:
                logger.info("All required cookies collected via Selenium")

            self._save_cookies_to_file(filtered)
            return filtered

        except Exception as e:
            logger.error(f"Error in Selenium cookie fetch: {e}")
            return None

    def get_nse_cookies(self) -> Optional[Dict[str, str]]:
        """
        Get NSE cookies - tries HTTP first, falls back to Selenium if available.
        """
        # Try HTTP method first (works on low-memory VMs)
        cookies = self.get_cookies_via_http()
        if cookies and self.validate_cookies(cookies):
            logger.info("Successfully obtained valid cookies via HTTP")
            return cookies
        
        # Fall back to Selenium if available
        if SELENIUM_AVAILABLE:
            logger.info("HTTP cookies invalid, trying Selenium...")
            cookies = self.get_cookies_via_selenium()
            if cookies:
                return cookies
        
        # Last resort: return whatever HTTP gave us (may work for some endpoints)
        if cookies:
            logger.warning("Returning unvalidated HTTP cookies as last resort")
            return cookies
            
        logger.error("Failed to obtain valid cookies")
        return None

    def _save_cookies_to_file(self, cookies: Dict[str, str]):
        try:
            data = {
                "cookies": cookies,
                "timestamp": datetime.now().isoformat(),
                "expiry": time.time() + 3600  # 1-hour expiry
            }
            with open(self.cookies_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cookies saved to {self.cookies_file}")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def load_cookies_from_file(self) -> Optional[Dict[str, str]]:
        if not os.path.exists(self.cookies_file):
            logger.info("Cookie file not found")
            return None
        try:
            with open(self.cookies_file, "r") as f:
                data = json.load(f)
            if time.time() > data.get("expiry", 0):
                logger.info("Stored cookies expired")
                return None
            cookies = data.get("cookies")
            if cookies:
                logger.info("Loaded cookies from file")
                return cookies
            return None
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return None

    def validate_cookies(self, cookies: Dict[str, str]) -> bool:
        try:
            test_url = f"{self.base_url}/api/allIndices"
            resp = self.session.get(test_url, headers=NSE_GET_COOKIES_HEADERS, cookies=cookies, timeout=10)
            if resp.status_code == 200:
                logger.info("Cookies validation successful")
                return True
            logger.warning(f"Cookie validation failed: status {resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"Error validating cookies: {e}")
            return False

    def refresh_cookies(self) -> Optional[Dict[str, str]]:
        logger.info("Refreshing cookies...")
        return self.get_nse_cookies()


cookie_service = NSECookieService()


def get_nse_cookies() -> Optional[Dict[str, str]]:
    """Get valid NSE cookies - main entry point."""
    # First try to load from file
    cookies = cookie_service.load_cookies_from_file()
    if cookies and cookie_service.validate_cookies(cookies):
        return cookies
    
    # Fetch fresh cookies
    logger.info("Fetching fresh cookies")
    cookies = cookie_service.refresh_cookies()
    if cookies:
        return cookies
    
    logger.error("Unable to obtain valid cookies")
    return None


def refresh_nse_cookies() -> Optional[Dict[str, str]]:
    """Force refresh NSE cookies."""
    return cookie_service.refresh_cookies()


if __name__ == "__main__":
    logger.info("Running NSECookieService tests")
    cookies = get_nse_cookies()
    print(f"Got {len(cookies) if cookies else 0} cookies")
    if cookies:
        print("Validation result:", cookie_service.validate_cookies(cookies))
