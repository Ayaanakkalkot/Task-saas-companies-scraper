"""
Browser Utilities Module
Contains functions for browser simulation and anti-detection
"""

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def simulate_real_browser_behavior(driver):
    """Simulate realistic browser behavior to avoid detection"""
    try:
        # Random mouse movements
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            driver.execute_script(f"document.elementFromPoint({x}, {y}).dispatchEvent(new MouseEvent('mouseover', {{bubbles: true}}));")
            time.sleep(random.uniform(0.1, 0.3))
        
        # Random scrolling
        scroll_amount = random.randint(100, 300)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(0.5, 1.0))
        
        # Random page interactions
        elements = driver.find_elements(By.TAG_NAME, "div")
        if elements:
            random_element = random.choice(elements[:20])
            try:
                actions = ActionChains(driver)
                actions.move_to_element(random_element).perform()
                time.sleep(random.uniform(0.2, 0.5))
            except:
                pass
                
    except Exception as e:
        print(f" Error in browser simulation: {e}")

def wait_for_page_load_with_retry(driver, expected_elements: str, max_wait: int = 30) -> bool:
    """Wait for page to load with multiple verification methods"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            # Wait for elements to appear
            WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, expected_elements))
            )
            
            # Verify page source is substantial
            page_source = driver.page_source
            if len(page_source) < 5000:  # Too short, likely blocked
                print(f" Page source too short ({len(page_source)} chars), waiting...")
                time.sleep(2)
                continue
            
            # Check for blocking indicators
            if any(indicator in page_source.lower() for indicator in ['blocked', 'captcha', 'cloudflare']):
                print(" Blocking detected, waiting...")
                time.sleep(3)
                continue
            
            return True
            
        except TimeoutException:
            print(" Waiting for page content...")
            time.sleep(2)
            continue
        except Exception as e:
            print(f" Error waiting for page: {e}")
            time.sleep(2)
            continue
    
    return False

def handle_potential_overlays(driver):
    """Handle potential overlays, popups, or modals that might block clicks"""
    try:
        # Try to close any modals or popups
        modal_selectors = [
            "button[aria-label='Close']",
            ".modal-close",
            ".popup-close",
            ".overlay-close",
            "[data-dismiss='modal']",
            ".btn-close"
        ]
        
        for selector in modal_selectors:
            try:
                close_button = driver.find_element(By.CSS_SELECTOR, selector)
                if close_button.is_displayed():
                    print(f" Found and closing overlay: {selector}")
                    close_button.click()
                    time.sleep(1)
            except:
                continue
        
        # Try to escape any overlays
        try:
            actions = ActionChains(driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
        except:
            pass
            
    except Exception as e:
        print(f" Error handling overlays: {e}")

def detect_blocking(driver) -> bool:
    """Detect if the current page is blocked"""
    try:
        page_source = driver.page_source
        
        # Check for blocking indicators
        blocking_indicators = [
            'blocked', 'captcha', 'cloudflare', 'access denied',
            'please wait', 'checking your browser', 'ddos protection'
        ]
        
        for indicator in blocking_indicators:
            if indicator in page_source.lower():
                print(f" Blocking detected: {indicator}")
                return True
        
        # Check if page source is too short (likely blocked)
        if len(page_source) < 5000:
            print(f" Page source too short ({len(page_source)} chars) - likely blocked")
            return True
        
        # Check if company rows are missing
        company_rows = driver.find_elements(By.CLASS_NAME, "data-table_row__aX_dq")
        if not company_rows:
            print(" No company rows found - likely blocked")
            return True
        
        return False
        
    except Exception as e:
        print(f" Error detecting blocking: {e}")
        return True

def wait_for_ajax_content_load(driver, expected_count: int = 20, timeout: int = 30) -> bool:
    """Wait for AJAX content to load after clicking pagination"""
    start_time = time.time()
    last_count = 0
    
    while time.time() - start_time < timeout:
        try:
            # Get current company rows
            current_rows = driver.find_elements(By.CLASS_NAME, "data-table_row__aX_dq")
            current_count = len(current_rows)
            
            print(f" Current company rows: {current_count}")
            
            # Check if content changed
            if current_count > last_count:
                print(f" Content updated: {last_count} -> {current_count} rows")
                last_count = current_count
                
                # If we have the expected number of rows, content loaded successfully
                if current_count >= expected_count:
                    print(f" AJAX content loaded successfully: {current_count} rows")
                    return True
            
            # Simulate realistic behavior while waiting
            simulate_real_browser_behavior(driver)
            time.sleep(2)
            
        except Exception as e:
            print(f" Error waiting for AJAX content: {e}")
            time.sleep(2)
    
    print(f" Timeout waiting for AJAX content. Final count: {last_count}")
    return False 