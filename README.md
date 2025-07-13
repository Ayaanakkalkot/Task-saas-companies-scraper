# SaaS Company Web Scraper

A comprehensive Python-based web scraper for extracting SaaS company information from [getlatka.com](https://getlatka.com/saas-companies) and its associated company pages.

## Project Overview

I have build a web scraper based on the task i have been assigned this inclueds perfectly scarping of 100 companies which handles pagination, missing values and also anit bots mechanism.

## Features

- **Modular Architecture**: Well-organized code structure with separate modules for core functionality
- **Flexible Scraping**: Scrape specific pages or page ranges
- **Base Scraping**: Default behavior scrapes pages 1-5 (100 companies total)
- **Extended Scraping**: Scrapes detailed profiles from individual company pages
- **Multithreaded Processing**: Uses concurrent.futures for improved performance
- **Pagination Handling**: Automatically navigates through multiple pages
- **Missing Data Handling**: Gracefully handles missing/null values
- **Anti-Bot Protection**: Uses Selenium with realistic browser behavior
- **Configurable Parameters**: Easy to modify scraping behavior
- **JSON Output**: Structured data in JSON format
- **Comprehensive Logging**: Thread-safe logging for debugging and monitoring

## Requirements

### System Requirements
- Python 3.7+
- Chrome browser (for Selenium)
- Windows/Linux/macOS

### Python Dependencies
- requests==2.31.0
- beautifulsoup4==4.12.2
- selenium==4.15.2
- lxml==4.9.3
- urllib3==2.0.7

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Zintlr-WebScrapper-Task
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. ChromeDriver Setup
The project includes a `chromedriver.exe` file for Windows. For other operating systems:

**Linux/macOS:**
```bash
# Download ChromeDriver
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
wget https://chromedriver.storage.googleapis.com/$(cat LATEST_RELEASE)/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
```

**macOS (using Homebrew):**
```bash
brew install chromedriver
```

## Usage

### Basic Usage (Default: Pages 1-5)
```bash
python main.py
```

### Scrape Specific Page
```bash
python main.py <page_number>
```

### Scrape Page Range
```bash
python main.py <start_page> <end_page>
```

##  Output Structure

### 1. Base Companies List('companies_pages_1_to_5.json')
Contains the main company data from the listing pages:

```json
[
  {
    "Company Name": "SubMagic",
    "Company Linkedin Url": "https://www.linkedin.com/company/submagic/",
    "Company Hyperlink": "https://getlatka.com/companies/submagic.co",
    "Company Website URL": "https://www.submagic.co/",
    "Revenue": "$8M",
    "Funding": "$571.4K",
    "Growth": null,   
    "Founder Name": null,
    "Location": "France",
    "Industry": "Artificial Intelligence"
  }
]
```

### 2. Detailed Companies (`detailed_companies.json`)
Contains base data plus detailed profile information:

```json
[
  {
    "Company Name": "SubMagic",
    "Company Linkedin Url": "https://www.linkedin.com/company/submagic/",
    "Company Hyperlink": "https://getlatka.com/companies/submagic.co",
    "Company Website URL": "https://www.submagic.co/",
    "Revenue": "$8M",
    "Funding": "$571.4K",
    "Growth": null,
    "Founder Name": null,
    "Location": "France",
    "Industry": "Artificial Intelligence",
    "employee_count": "50 employees",
    "ceo_name": "John Doe",
    "founded_year": "Founded in 2020",
    "pricing_info": "$29/month",
    "top_products": "AI-powered content creation",
    "description": "SubMagic is an AI-powered...", 
    }
  }
]
```

## Technical Details

### Architecture
- **Modular Design**: Separate modules for core functionality, utilities, and data extraction
- **Error Handling**: Comprehensive exception handling and logging
- **Configurable**: Easy to modify scraping parameters
- **Respectful Scraping**: Includes delays and realistic user agents

### Technology Choices
- **BeautifulSoup**: For HTML parsing (chosen over Scrapy for simplicity and flexibility)
- **Selenium**: For handling dynamic content and anti-bot measures
- **Requests**: For basic HTTP requests
- **concurrent.futures**: For multithreaded processing
- **JSON**: For structured data output

### Anti-Bot Measures Handled
- User-Agent rotation
- Realistic request delays
- Headless browser simulation
- Session management

## Anti-Bot & Security Measures

### CAPTCHA Detection & Handling

1. **Visual CAPTCHA Detection**
   - Automated detection of CAPTCHA presence using image recognition
   - Logs CAPTCHA encounters for monitoring
   - Implements exponential backoff when CAPTCHAs are detected

2. **Browser Fingerprinting Protection**
   - Rotates User-Agent strings randomly
   - Maintains consistent viewport sizes
   - Simulates natural mouse movements and scrolling
   - Randomizes typing speed for form inputs

3. **Rate Limiting & Delays**
   - Dynamic delay between requests (2-5 seconds)
   - Exponential backoff on 429 responses
   - Random jitter added to delays
   - Session cooldown periods after intensive scraping

4. **Session Management**
   - Maintains persistent sessions
   - Handles cookies appropriately
   - Rotates IP addresses when possible
   - Clears browser data periodically

### Common Anti-Bot Triggers

1. **Request Patterns**
   - Too many requests in short time
   - Perfectly timed intervals between requests
   - Accessing pages in strict numerical order

2. **Browser Behavior**
   - Missing or suspicious headers
   - Inconsistent browser fingerprints
   - Lack of mouse movements
   - Instant form filling

3. **Technical Indicators**
   - WebDriver presence detection
   - JavaScript execution checks
   - Canvas fingerprinting
   - Browser automation flags

### Mitigation Strategies

1. **Human-Like Behavior**
   ```python
   # Example delay implementation
   import random
   import time
   
   def human_delay():
       base_delay = random.uniform(2, 5)
       jitter = random.uniform(-0.5, 0.5)
       time.sleep(base_delay + jitter)
   ```

2. **Progressive Loading**
   - Scroll pages gradually
   - Wait for dynamic content
   - Interact with page elements naturally
   - Handle lazy-loading content

3. **Error Recovery**
   - Automatic retry with backoff
   - Session refresh on detection
   - Alternative path navigation
   - Proxy rotation when needed

### Monitoring & Logging

1. **Detection Events**
   ```json
   {
     "timestamp": "2024-01-20T10:15:30Z",
     "event_type": "captcha_detected",
     "url": "https://example.com/page/5",
     "retry_count": 1,
     "backoff_duration": 300
   }
   ```

2. **Success Metrics**
   - CAPTCHA encounter rate
   - Success rate per session
   - Average delay between requests
   - Session duration statistics

### Configuration Options

```python
ANTI_BOT_CONFIG = {
    'min_delay': 2,
    'max_delay': 5,
    'max_retries': 3,
    'backoff_factor': 2,
    'session_cooldown': 300,
    'rotate_user_agent': True,
    'simulate_human_behavior': True
}
```

### Best Practices

1. **Respect Robots.txt**
   - Always check and follow robots.txt rules
   - Honor crawl-delay directives
   - Avoid restricted paths

2. **Ethical Considerations**
   - Identify scraper in User-Agent
   - Don't overload servers
   - Cache results when possible
   - Limit concurrent requests

3. **Legal Compliance**
   - Review terms of service
   - Respect rate limits
   - Store data responsibly
   - Document compliance measures

## Assumptions Made

1. **HTML Structure**: The scraper assumes certain HTML patterns based on common SaaS listing sites
2. **Data Availability**: Some fields may be missing from certain companies
3. **Rate Limiting**: Includes delays to respect the target website
4. **Dynamic Content**: Uses Selenium to handle JavaScript-rendered content

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**
   - Ensure `chromedriver.exe` is in the project directory
   - For other OS, install ChromeDriver separately

2. **No companies found**
   - Check if the website structure has changed
   - Verify internet connection
   - Check logs for specific errors

3. **Selenium errors**
   - Update Chrome browser to latest version
   - Ensure ChromeDriver version matches Chrome version

### Logs
Check `scraper.log` for detailed error information and scraping progress.

## Performance

- **Expected Time**: ~5-8 minutes for 100 companies (with multithreading)
- **Memory Usage**: Low (streaming processing)
- **Success Rate**: 90%+ (depends on website availability)
- **Concurrency**: Configurable thread pool (default: 4 workers)

## Ethical Considerations

- Respects robots.txt
- Includes delays between requests
- Uses realistic user agents
- Does not overwhelm the target server

## License

This project is created for the Zintlr Data Engineering Intern Task.

## Author

Data Engineering Intern - Ayaan Akkalkot  
Zintlr Web Scraper Task  
2025

---
