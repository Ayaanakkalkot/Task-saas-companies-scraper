"""
SaaS Company Scraper
Main scraper class that inherits from BaseScraper
"""

from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base_scraper import BaseScraper
from browser_utils import (
    simulate_real_browser_behavior,
    wait_for_page_load_with_retry,
    handle_potential_overlays,
    detect_blocking,
    wait_for_ajax_content_load
)
from data_extractor import extract_company_data_from_card, extract_company_profile

class SaaSCompanyScraper(BaseScraper):
    """Main scraper class for SaaS company data"""
    
    def _process_companies_chunk(self, companies_chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a chunk of companies with detailed profile scraping"""
        detailed_companies = []
        
        for company in companies_chunk:
            try:
                if company.get('Company Hyperlink'):
                    profile_url = company['Company Hyperlink']
                    self._thread_safe_log(f"Scraping company profile: {profile_url}")
                    
                    time.sleep(self.config['delay_between_requests'])
                    
                    # Scrape detailed profile
                    content = self._get_page_content(profile_url)
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        profile_data = extract_company_profile(soup)
                        detailed_company = {**company, **profile_data}
                        detailed_companies.append(detailed_company)
                    else:
                        detailed_companies.append(company)
                else:
                    detailed_companies.append(company)
                    
            except Exception as e:
                self._thread_safe_log(f"Error processing company {company.get('Company Name', 'Unknown')}: {e}", 'error')
                detailed_companies.append(company)
        
        return detailed_companies

    def scrape_companies_list(self) -> List[Dict[str, Any]]:
        """Scrape the main companies list from all specified pages"""
        all_companies = []

        if self.config['use_selenium'] and self.driver:
            print("Attempting Selenium-based scraping...")

            try:
                self._thread_safe_log(f"Navigating to {self.config['base_url']}")
                self.driver.get(self.config['base_url'])
                time.sleep(5)

                for page in range(1, self.config['pages_to_scrape'] + 1):
                    self._thread_safe_log(f"Scraping page {page}...")
                    print(f" Starting to scrape page {page}...")
                    
                    try:
                        print(f" Waiting for company rows on page {page}...")
                        WebDriverWait(self.driver, 15).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "data-table_row__aX_dq"))
                        )
                        print(f" Company rows found on page {page}")
                    except TimeoutException:
                        print(f" Timeout waiting for company rows on page {page}")
                        page_source = self.driver.page_source
                        print(f" Page source length: {len(page_source)} characters")
                        
                        if len(page_source) < 5000:
                            print(" Page appears to be blocked (short content)")
                            if page > 1:
                                print(" Switching to requests-based scraping...")
                                return self._scrape_with_requests_fallback()
                            else:
                                break
                        else:
                            print(" Company rows not found, but page loaded")
                            continue
                    
                    rows = self.driver.find_elements(By.CLASS_NAME, "data-table_row__aX_dq")
                    self._thread_safe_log(f"Found {len(rows)} companies on page {page}")
                    print(f" Found {len(rows)} companies on page {page}")
                    
                    page_companies = []
                    for row in rows:
                        try:
                            row_html = row.get_attribute('outerHTML')
                            soup = BeautifulSoup(row_html, 'html.parser')
                            company_data = extract_company_data_from_card(soup)
                            if company_data['Company Name']:
                                page_companies.append(company_data)
                        except Exception as e:
                            self._thread_safe_log(f"Error extracting data from row: {e}", 'warning')
                            continue
                    
                    if page_companies:
                        all_companies.extend(page_companies)
                        print(f" Successfully extracted {len(page_companies)} companies from page {page}")
                    else:
                        print(f" No companies extracted from page {page}")

                    if page < self.config['pages_to_scrape']:
                        if not self._navigate_to_next_page(page):
                            print(f"Failed to navigate to page {page + 1}")
                            print(" Switching to requests-based scraping...")
                            return self._scrape_with_requests_fallback()
                    
                    time.sleep(self.config['delay_between_requests'])
                    
            except Exception as e:
                print(f" Selenium scraping failed: {e}")
                self._thread_safe_log(f"Selenium scraping error: {e}", 'error')
        
        if not all_companies:
            print(" Selenium failed or unavailable, trying requests-based scraping...")
            all_companies = self._scrape_with_requests_fallback()
        
        self._thread_safe_log(f"Total companies scraped: {len(all_companies)}")
        return all_companies

    def _navigate_to_next_page(self, current_page: int) -> bool:
        """Navigate to the next page with proper verification"""
        print(f" Navigating from page {current_page} to page {current_page + 1}...")
        
        try:
            handle_potential_overlays(self.driver)
            simulate_real_browser_behavior(self.driver)
            
            # Get current company names for comparison
            current_rows = self.driver.find_elements(By.CLASS_NAME, "data-table_row__aX_dq")
            previous_companies = []
            for row in current_rows[:5]:
                try:
                    company_name = row.find_element(By.CSS_SELECTOR, "a.cells_link__PfQot").text.strip()
                    previous_companies.append(company_name)
                except:
                    continue
            
            next_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination_button__gUpxa.pagination_special_button__XQ4Z3.pagination-next-link"))
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(2)
            
            click_success = False
            
            try:
                print(" Attempting JavaScript click...")
                self.driver.execute_script("arguments[0].click();", next_button)
                print(" JavaScript click successful")
                click_success = True
            except Exception as e:
                print(f" JavaScript click failed: {e}")
            
            if not click_success:
                try:
                    print(" Attempting standard click...")
                    next_button.click()
                    print(" Standard click successful")
                    click_success = True
                except Exception as e:
                    print(f" Standard click failed: {e}")
            
            if not click_success:
                print(" All click methods failed")
                return False
            
            print(" Waiting for AJAX content to load...")
            if wait_for_ajax_content_load(self.driver, 20, 30):
                print(" AJAX content loaded successfully")
                
                # Verify content actually changed
                current_rows = self.driver.find_elements(By.CLASS_NAME, "data-table_row__aX_dq")
                current_companies = []
                for row in current_rows[:5]:
                    try:
                        company_name = row.find_element(By.CSS_SELECTOR, "a.cells_link__PfQot").text.strip()
                        current_companies.append(company_name)
                    except:
                        continue
                
                if current_companies and previous_companies:
                    if current_companies[0] != previous_companies[0]:
                        print(f" Successfully navigated to page {current_page + 1}")
                        return True
                
                print(" Content didn't change - might be blocked or at last page")
                return False
            else:
                print(" AJAX content failed to load")
                return False
        
        except Exception as e:
            print(f" Error navigating to next page: {e}")
            return False

    def _scrape_with_requests_fallback(self) -> List[Dict[str, Any]]:
        """Scrape using requests as a fallback when Selenium is blocked"""
        print(" Trying requests-based scraping as fallback...")
        all_companies = []
        
        for page in range(1, self.config['pages_to_scrape'] + 1):
            print(f" Scraping page {page} with requests...")
            
            url = f"{self.config['base_url']}?page={page}" if page > 1 else self.config['base_url']
            content = self._get_page_content(url)
            if not content:
                print(f" Failed to get content for page {page}")
                continue
            
            soup = BeautifulSoup(content, 'html.parser')
            company_rows = soup.find_all('tr', class_='data-table_row__aX_dq')
            
            if not company_rows:
                print(f" No company rows found on page {page}")
                continue
            
            print(f" Found {len(company_rows)} companies on page {page}")
            
            page_companies = []
            for row in company_rows:
                try:
                    company_data = extract_company_data_from_card(row)
                    if company_data['Company Name']:
                        page_companies.append(company_data)
                except Exception as e:
                    print(f" Error extracting data from row: {e}")
                    continue
            
            if page_companies:
                all_companies.extend(page_companies)
                print(f" Successfully extracted {len(page_companies)} companies from page {page}")
            else:
                print(f" No companies extracted from page {page}")
            
            time.sleep(self.config['delay_between_requests'])
        
        return all_companies

    def scrape_all_company_profiles(self, companies_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scrape detailed profiles for all companies"""
        if not companies_list:
            return []

        self._thread_safe_log(f"Starting profile scraping for {len(companies_list)} companies...")

        detailed_companies = []

        if self.config.get('use_selenium') and self.driver:
            for company in companies_list:
                try:
                    profile_url = company.get('Company Hyperlink')
                    detailed_data = self.scrape_company_profile(profile_url) if profile_url else {}
                    merged = {**company, **detailed_data}
                    detailed_companies.append(merged)
                except Exception as e:
                    self._thread_safe_log(f"Error processing company {company.get('Company Name', 'Unknown')}: {e}", 'error')
                    detailed_companies.append(company)
        else:
            chunk_size = self.config.get('chunk_size', 5)
            company_chunks = [companies_list[i:i + chunk_size] for i in range(0, len(companies_list), chunk_size)]
            max_workers = self.config.get('max_workers', 4)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_chunk = {
                    executor.submit(self._process_companies_chunk, chunk): i 
                    for i, chunk in enumerate(company_chunks)
                }
                for future in as_completed(future_to_chunk):
                    chunk_index = future_to_chunk[future]
                    try:
                        chunk_results = future.result()
                        detailed_companies.extend(chunk_results)
                        self._thread_safe_log(f"Completed processing chunk {chunk_index + 1}/{len(company_chunks)}")
                    except Exception as e:
                        self._thread_safe_log(f"Error processing chunk {chunk_index + 1}: {e}", 'error')

        self._thread_safe_log(f"Completed profile scraping. Total companies processed: {len(detailed_companies)}")
        return detailed_companies

    def scrape_company_profile(self, company_url: str) -> Dict[str, Any]:
        """Scrape detailed information from an individual company page"""
        self._thread_safe_log(f"Scraping company profile: {company_url}")

        content = None
        if self.config.get('use_selenium') and self.driver:
            try:
                self.driver.get(company_url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "section#details"))
                )
                content = self.driver.page_source
            except Exception as e:
                print(f"[DEBUG] Failed to load profile page for {company_url}: {e}")
                return {}
        else:
            content = self._get_page_content(company_url)
            if not content:
                return {}

        soup = BeautifulSoup(content, 'html.parser')
        return extract_company_profile(soup)

    def scrape_specific_page(self, page_number: int) -> List[Dict[str, Any]]:
        """
        Scrape a specific page number
        
        Args:
            page_number: The page number to scrape (1-based index)
            
        Returns:
            List of companies from that page
        """
        if page_number < 1:
            raise ValueError("Page number must be 1 or greater")
            
        print(f"\nScraping page {page_number}...")
        
        # Construct URL for the specific page
        url = self.config['base_url']
        if page_number > 1:
            url = f"{url}?page={page_number}"
            
        companies = []
        
        # Try Selenium first
        if self.config['use_selenium'] and self.driver:
            try:
                print(f"Navigating to page {page_number} with Selenium...")
                self.driver.get(url)
                time.sleep(5)  # Wait for initial load
                
                # Wait for company rows
                print("Waiting for company rows...")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "data-table_row__aX_dq"))
                )
                
                # Get all rows
                rows = self.driver.find_elements(By.CLASS_NAME, "data-table_row__aX_dq")
                print(f"Found {len(rows)} companies on page {page_number}")
                
                # Extract data from each row
                for row in rows:
                    try:
                        row_html = row.get_attribute('outerHTML')
                        soup = BeautifulSoup(row_html, 'html.parser')
                        company_data = extract_company_data_from_card(soup)
                        if company_data['Company Name']:
                            companies.append(company_data)
                    except Exception as e:
                        print(f"Error extracting data from row: {e}")
                        continue
                        
            except Exception as e:
                print(f"Selenium scraping failed: {e}")
                print("Falling back to requests...")
        
        # If Selenium failed or wasn't available, try requests
        if not companies:
            try:
                print(f"Scraping page {page_number} with requests...")
                content = self._get_page_content(url)
                
                if content:
                    soup = BeautifulSoup(content, 'html.parser')
                    rows = soup.find_all('tr', class_='data-table_row__aX_dq')
                    
                    print(f"Found {len(rows)} companies")
                    
                    for row in rows:
                        try:
                            company_data = extract_company_data_from_card(row)
                            if company_data['Company Name']:
                                companies.append(company_data)
                        except Exception as e:
                            print(f"Error extracting data from row: {e}")
                            continue
                            
            except Exception as e:
                print(f"Requests scraping failed: {e}")
        
        # Save results for this page
        if companies:
            print(f"\nSuccessfully scraped {len(companies)} companies from page {page_number}")
            self.save_to_json(companies, f'companies_page_{page_number}.json')
        else:
            print(f"\nNo companies found on page {page_number}")
        
        return companies

    def scrape_page_range(self, start_page: int, end_page: int) -> List[Dict[str, Any]]:
        """
        Scrape a range of pages from start_page to end_page (inclusive)
        
        Args:
            start_page: Starting page number (1-based index)
            end_page: Ending page number (inclusive)
            
        Returns:
            List of all companies from the specified range of pages
        """
        if start_page < 1:
            raise ValueError("Start page must be 1 or greater")
        if end_page < start_page:
            raise ValueError("End page must be greater than or equal to start page")
            
        all_companies = []
        
        print(f"\nScraping pages {start_page} to {end_page}...")
        
        for page_number in range(start_page, end_page + 1):
            print(f"\n{'='*50}")
            print(f"Processing page {page_number} of {end_page}")
            print(f"{'='*50}\n")
            
            try:
                # Scrape the current page
                companies = self.scrape_specific_page(page_number)
                
                if companies:
                    all_companies.extend(companies)
                    print(f"Total companies collected so far: {len(all_companies)}")
                else:
                    print(f"No companies found on page {page_number}")
                
                # Add a delay between pages
                if page_number < end_page:
                    delay = self.config['delay_between_requests']
                    print(f"\nWaiting {delay} seconds before next page...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"Error scraping page {page_number}: {e}")
                print("Continuing with next page...")
                continue
        
        # Save all results
        if all_companies:
            print(f"\nSuccessfully scraped {len(all_companies)} companies from pages {start_page}-{end_page}")
            self.save_to_json(all_companies, f'companies_pages_{start_page}_to_{end_page}.json')
        else:
            print(f"\nNo companies found in pages {start_page}-{end_page}")
        
        return all_companies

    def run_single_page(self, page_number: int):
        """
        Run the scraper for a single page
        
        Args:
            page_number: The page number to scrape (1-based index)
        """
        try:
            self._thread_safe_log(f"Starting scraper for page {page_number}...")
            
            # Scrape the specified page
            companies = self.scrape_specific_page(page_number)
            
            if not companies:
                self._thread_safe_log("No companies found.", 'error')
                return
            
            # Optionally scrape detailed profiles
            print("\nWould you like to scrape detailed profiles for these companies? (y/n)")
            response = input().lower().strip()
            
            if response == 'y':
                print("\nScraping detailed profiles...")
                detailed_companies = self.scrape_all_company_profiles(companies)
                self.save_to_json(detailed_companies, f'detailed_companies_page_{page_number}.json')
                print(f"\nSaved {len(detailed_companies)} detailed company profiles")
            
            print("\nScraping completed!")
            
        except Exception as e:
            self._thread_safe_log(f"Error during scraping: {e}", 'error')
            raise
        finally:
            self.close()
            self._thread_safe_log("WebDriver closed")

    def run_page_range(self, start_page: int, end_page: int):
        """
        Run the scraper for a range of pages
        
        Args:
            start_page: Starting page number (1-based index)
            end_page: Ending page number (inclusive)
        """
        try:
            self._thread_safe_log(f"Starting scraper for pages {start_page} to {end_page}...")
            
            # Scrape the specified range
            companies = self.scrape_page_range(start_page, end_page)
            
            if not companies:
                self._thread_safe_log("No companies found.", 'error')
                return
            
            # Optionally scrape detailed profiles
            print("\nWould you like to scrape detailed profiles for these companies? (y/n)")
            response = input().lower().strip()
            
            if response == 'y':
                print("\nScraping detailed profiles...")
                detailed_companies = self.scrape_all_company_profiles(companies)
                self.save_to_json(detailed_companies, f'detailed_companies_pages_{start_page}_to_{end_page}.json')
                print(f"\nSaved {len(detailed_companies)} detailed company profiles")
            
            print("\nScraping completed!")
            
        except Exception as e:
            self._thread_safe_log(f"Error during scraping: {e}", 'error')
            raise
        finally:
            self.close()
            self._thread_safe_log("WebDriver closed")

    def run(self):
        """Main execution method for the scraper"""
        try:
            self._thread_safe_log("Starting SaaS Company Scraper...")
            
            # Step 1: Scrape the main companies list
            self._thread_safe_log("Step 1: Scraping main companies list...")
            companies_list = self.scrape_companies_list()
            
            if not companies_list:
                self._thread_safe_log("No companies found. Exiting.", 'error')
                return
            
            # Save base companies list
            self.save_to_json(companies_list, 'companies_list.json')
            
            # Step 2: Scrape detailed profiles with multithreading
            self._thread_safe_log("Step 2: Scraping detailed company profiles using multithreading...")
            detailed_companies = self.scrape_all_company_profiles(companies_list)
            
            # Save detailed companies data
            self.save_to_json(detailed_companies, 'detailed_companies.json')
            
            self._thread_safe_log("Scraping process completed successfully!")
            self._thread_safe_log(f"Base companies saved: {len(companies_list)}")
            self._thread_safe_log(f"Detailed profiles saved: {len(detailed_companies)}")
            
        except Exception as e:
            self._thread_safe_log(f"Error during scraping: {e}", 'error')
            raise
        finally:
            # Clean up
            self.close()
            self._thread_safe_log("WebDriver closed") 