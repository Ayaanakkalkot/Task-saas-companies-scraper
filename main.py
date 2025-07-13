"""
Main Entry Point
Runs the SaaS company scraper
"""

import sys
from saas_scraper import SaaSCompanyScraper

def print_usage():
    """Print usage instructions"""
    print("\nUsage:")
    print("1. Scrape all pages (default, pages 1-5):")
    print("   python main.py")
    print("\n2. Scrape a single page:")
    print("   python main.py <page_number>")
    print("   Example: python main.py 2")
    print("\n3. Scrape a range of pages:")
    print("   python main.py <start_page> <end_page>")
    print("   Example: python main.py 1 5")

def main():
    """Main function to run the scraper"""
    try:
        # Initialize scraper
        scraper = SaaSCompanyScraper()
        
        # Check command line arguments
        if len(sys.argv) == 1:
            # No arguments provided - use default behavior (pages 1-5)
            print("\nNo page numbers provided. Using default: pages 1-5")
            scraper.run_page_range(1, 5)
            
        elif len(sys.argv) == 2:
            # Single page mode
            try:
                page_number = int(sys.argv[1])
                if page_number < 1:
                    print("\nError: Page number must be 1 or greater")
                    print_usage()
                    return 1
                
                scraper.run_single_page(page_number)
                
            except ValueError:
                print("\nError: Please provide a valid page number")
                print_usage()
                return 1
                
        elif len(sys.argv) == 3:
            # Page range mode
            try:
                start_page = int(sys.argv[1])
                end_page = int(sys.argv[2])
                
                if start_page < 1:
                    print("\nError: Start page must be 1 or greater")
                    print_usage()
                    return 1
                    
                if end_page < start_page:
                    print("\nError: End page must be greater than or equal to start page")
                    print_usage()
                    return 1
                
                scraper.run_page_range(start_page, end_page)
                
            except ValueError:
                print("\nError: Please provide valid page numbers")
                print_usage()
                return 1
        else:
            print("\nError: Too many arguments")
            print_usage()
            return 1

        print("\nCheck the 'output' directory for results.")
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 