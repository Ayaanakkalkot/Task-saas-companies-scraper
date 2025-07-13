"""
Base Scraper Class
Contains core scraping functionality and browser management
"""

import json
import time
import logging
import threading
from typing import Dict, List, Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
import os
from bs4 import BeautifulSoup
import random
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Thread-safe lock for logging
log_lock = threading.Lock()

class BaseScraper:
    """Base scraper class with core functionality"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize base scraper with configuration"""
        self.config = config or {
            'base_url': 'https://getlatka.com/saas-companies',
            'pages_to_scrape': 5,
            'delay_between_requests': 2,
            'timeout': 10,
            'output_dir': 'output',
            'use_selenium': True,
            'headless': True,
            'max_workers': 4,
            'chunk_size': 5
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        self.driver = None
        self._setup_driver()
        
        # Thread-safe data structures
        self.companies_lock = threading.Lock()
        self.all_companies = []
        
        # Create output directory
        os.makedirs(self.config['output_dir'], exist_ok=True)
        
        self._thread_safe_log("Base Scraper initialized successfully")

    def _thread_safe_log(self, message: str, level: str = 'info'):
        """Thread-safe logging method"""
        with log_lock:
            if level == 'info':
                logger.info(message)
            elif level == 'warning':
                logger.warning(message)
            elif level == 'error':
                logger.error(message)
            elif level == 'debug':
                logger.debug(message)

    def _setup_driver(self):
        """Setup Selenium WebDriver using undetected-chromedriver"""
        if not self.config['use_selenium']:
            return
        try:
            options = uc.ChromeOptions()
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-extensions')
            
            self.driver = uc.Chrome(options=options)
            self.driver.set_window_size(1920, 1080)
            self.driver.set_window_position(0, 0)
            
            self._thread_safe_log("Selenium WebDriver setup completed with undetected-chromedriver")
            
        except Exception as e:
            self._thread_safe_log(f"Failed to setup undetected-chromedriver: {e}", 'warning')
            print(f" Failed to setup undetected-chromedriver: {e}")
            self.config['use_selenium'] = False

    def close(self):
        """Safely close the driver and cleanup resources"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception:
                # Ignore cleanup errors - this is expected on Windows
                pass

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.close()

    def save_to_json(self, data: List[Dict[str, Any]], filename: str):
        """Save data to JSON file"""
        filepath = os.path.join(self.config['output_dir'], filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self._thread_safe_log(f"Data saved to {filepath}")

    def _get_page_content(self, url: str) -> Optional[str]:
        """Get page content using either requests or Selenium with fallback mechanisms"""
        if self.config['use_selenium'] and self.driver:
            try:
                self._thread_safe_log(f"Attempting to fetch {url} with Selenium...")
                self.driver.get(url)
                time.sleep(self.config['delay_between_requests'])
                
                WebDriverWait(self.driver, self.config['timeout']).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                return self.driver.page_source
            except Exception as e:
                self._thread_safe_log(f"Selenium failed for {url}: {e}", 'warning')
        
        try:
            self._thread_safe_log(f"Attempting to fetch {url} with requests...")
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            return response.text
        except Exception as e:
            self._thread_safe_log(f"All methods failed for {url}: {e}", 'error')
            return None 