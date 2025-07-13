"""
Data Extractor Module
Contains functions for extracting company data from HTML elements
"""

import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def convert_employee_count(count_str: str) -> Optional[int]:
    """
    Convert employee count string to integer, handling K notation
    
    Args:
        count_str: String representation of employee count (e.g., '1.4K', '500', etc.)
        
    Returns:
        Integer value of employee count or None if conversion fails
    """
    try:
        # Remove any whitespace and convert to uppercase for consistency
        count_str = count_str.strip().upper()
        
        # Handle K notation (thousands)
        if 'K' in count_str:
            # Remove 'K' and convert to float first
            number = float(count_str.replace('K', ''))
            # Multiply by 1000 and convert to int
            return int(number * 1000)
        
        # Handle M notation (millions) if present
        if 'M' in count_str:
            number = float(count_str.replace('M', ''))
            return int(number * 1000000)
        
        # Handle simple numbers
        return int(count_str)
        
    except (ValueError, TypeError):
        print(f"Could not parse employee count: '{count_str}'")
        return None

def extract_company_data_from_card(card_element) -> Dict[str, Any]:
    """
    Extract company data from a table row element
    
    Args:
        card_element: BeautifulSoup element representing a table row
        
    Returns:
        Dictionary containing company data
    """
    company_data = {
        'Company Name': None,
        'Company Linkedin Url': None,
        'Company Hyperlink': None,
        'Company Website URL': None,
        'Revenue': None,
        'Funding': None,
        'Growth': None,
        'Founder Name': None,
        'Location': None,
        'Industry': None
    }
    
    try:
        # Get all table cells
        cells = card_element.find_all('td', class_='data-table_cell__a_9gs')
        if len(cells) < 14:  # Expected number of columns
            print(f"Expected 14 cells, found {len(cells)}")
            return company_data
        
        # Cell 1: Company name and links
        if len(cells) > 1:
            name_cell = cells[1]
            
            # Extract company name
            name_link = name_cell.find('a', class_='cells_link__PfQot')
            if name_link:
                company_data['Company Name'] = name_link.get_text(strip=True)
                # Extract company hyperlink
                href = name_link.get('href')
                if href:
                    if href.startswith('/'):
                        company_data['Company Hyperlink'] = urljoin('https://getlatka.com', href)
                    else:
                        company_data['Company Hyperlink'] = href
            
            # Extract LinkedIn URL
            linkedin_link = name_cell.find('a', href=re.compile(r'linkedin\.com'))
            if linkedin_link:
                company_data['Company Linkedin Url'] = linkedin_link.get('href')
            
            # Extract website URL
            website_link = name_cell.find('a', href=re.compile(r'//[^/]+'))
            if website_link:
                href = website_link.get('href')
                if href and href.startswith('//'):
                    company_data['Company Website URL'] = 'https:' + href
        
        # Cell 2: Revenue
        if len(cells) > 2:
            revenue_cell = cells[2]
            lock_button = revenue_cell.find('button', class_='btn_lock')
            if not lock_button:
                revenue_text = revenue_cell.get_text(strip=True)
                if revenue_text and revenue_text != '':
                    company_data['Revenue'] = revenue_text
        
        # Cell 6: Funding
        if len(cells) > 6:
            funding_cell = cells[6]
            lock_button = funding_cell.find('button', class_='btn_lock')
            if not lock_button:
                funding_text = funding_cell.get_text(strip=True)
                if funding_text and funding_text != '':
                    company_data['Funding'] = funding_text
        
        # Cell 8: Growth
        if len(cells) > 8:
            growth_cell = cells[8]
            lock_button = growth_cell.find('button', class_='btn_lock')
            if not lock_button:
                growth_text = growth_cell.get_text(strip=True)
                if growth_text and growth_text != '':
                    company_data['Growth'] = growth_text
        
        # Cell 9: Founder
        if len(cells) > 9:
            founder_cell = cells[9]
            founder_link = founder_cell.find('a', class_='cells_name__pBrsJ')
            if founder_link:
                founder_text = founder_link.get_text(strip=True)
                if founder_text and founder_text != '':
                    company_data['Founder Name'] = founder_text
        
        # Cell 13: Location
        if len(cells) > 13:
            location_cell = cells[13]
            location_link = location_cell.find('a')
            if location_link:
                location_text = location_link.get_text(strip=True)
                if location_text and location_text != '':
                    company_data['Location'] = location_text
        
        # Cell 14: Industry
        if len(cells) > 14:
            industry_cell = cells[14]
            industry_link = industry_cell.find('a', class_='saas-companies_ellipses__Y9AeV')
            if industry_link:
                industry_text = industry_link.get_text(strip=True)
                if industry_text and industry_text != '':
                    company_data['Industry'] = industry_text
        
    except Exception as e:
        print(f"Error extracting company data: {e}")
    
    return company_data

def extract_company_profile(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract detailed company profile data from profile page
    
    Args:
        soup: BeautifulSoup object of the profile page
        
    Returns:
        Dictionary containing profile data
    """
    profile_data = {
        'employee_count': None,
        'ceo_name': None,
        'founded_year': None,
        'pricing_info': None,
        'top_products': None,
        'description': None
    }
    
    try:
        # Extract description
        description_elem = soup.find('p', class_='p-text p-text_details')
        if description_elem:
            profile_data['description'] = description_elem.get_text(strip=True)
        
        # Find the details section
        details_section = soup.find('section', id='details')
        if details_section:
            indicators_container = details_section.find('div', class_='indicators')
            if indicators_container:
                indicators = indicators_container.find_all('div', class_='indicators__i')
                for indicator in indicators:
                    text_block = indicator.find('div', class_='indicators-text')
                    if not text_block:
                        continue
                    value_elem = text_block.find('h4', class_='h4')
                    label_elem = text_block.find('p', class_='p-indicators')
                    if not value_elem or not label_elem:
                        continue
                    value = value_elem.get_text(strip=True)
                    label = label_elem.get_text(strip=True).lower()
                    
                    if 'founded' in label:
                        profile_data['founded_year'] = value
                    elif 'revenue' in label:
                        profile_data['Revenue'] = value
                    elif 'yoy' in label:
                        profile_data['Growth'] = value
                    elif 'funding' in label:
                        profile_data['Funding'] = value
        
        # Extract employee count from table
        team_section = soup.select_one('section#team table tr:has(td.table__td_bullet:contains("Total team size")) td:nth-child(2)')
        if team_section:
            emp_count = team_section.get_text(strip=True)
            # Use the new convert_employee_count function
            profile_data['employee_count'] = convert_employee_count(emp_count)
    
    except Exception as e:
        print(f"Error extracting profile data: {e}")
    
    return profile_data 