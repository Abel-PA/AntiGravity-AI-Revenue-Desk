#!/usr/bin/env python3
"""
Google My Business Lead Scraper
Extracts business listing details from Google Maps/GMB profiles.
"""

import argparse
import time
import random
import sys
from datetime import datetime
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("ERROR: Selenium not installed. Run: pip install selenium")
    sys.exit(1)


class GMBScraper:
    """Scrapes Google My Business listings for lead generation."""
    
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome WebDriver."""
        self.driver = self._setup_driver(headless)
        self.results = []
        
    def _setup_driver(self, headless):
        """Configure and return Chrome WebDriver."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            print(f"ERROR: Failed to initialize Chrome WebDriver: {e}")
            print("Make sure Chrome and ChromeDriver are installed.")
            print("Install with: brew install chromedriver (Mac) or download from https://chromedriver.chromium.org/")
            sys.exit(1)
    
    def search(self, query, max_results=20):
        """Search Google Maps for businesses matching the query."""
        print(f"\n🔍 Searching for: {query}")
        print(f"📊 Target: {max_results} results\n")
        
        # Construct Google Maps search URL
        search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        
        try:
            self.driver.get(search_url)
            time.sleep(3)  # Wait for initial load
            
            # Scroll to load more results
            self._scroll_results_panel(max_results)
            
            # Extract business listings
            self._extract_listings(max_results)
            
        except Exception as e:
            print(f"ERROR during search: {e}")
            
        return self.results
    
    def _scroll_results_panel(self, max_results):
        """Scroll the results panel to load more businesses."""
        print("📜 Loading results...")
        
        try:
            # Find the scrollable results panel
            results_panel = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
            )
            
            last_height = 0
            scroll_attempts = 0
            max_scrolls = 50  # Prevent infinite scrolling
            
            while scroll_attempts < max_scrolls:
                # Scroll down in the results panel
                self.driver.execute_script(
                    "arguments[0].scrollTo(0, arguments[0].scrollHeight);", 
                    results_panel
                )
                
                time.sleep(random.uniform(1.5, 2.5))  # Random delay
                
                # Check if we've loaded enough results
                current_results = len(self.driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] > div > div > a"))
                
                if current_results >= max_results:
                    print(f"✅ Loaded {current_results} results")
                    break
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", results_panel
                )
                
                if new_height == last_height:
                    print(f"⚠️  Reached end of results ({current_results} found)")
                    break
                    
                last_height = new_height
                scroll_attempts += 1
                
        except TimeoutException:
            print("⚠️  Could not find results panel")
    
    def _extract_listings(self, max_results):
        """Extract business details from loaded listings."""
        print("\n📋 Extracting business details...\n")
        
        try:
            # Find the results panel for scrolling
            results_panel = self.driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
            
            for idx in range(max_results):
                try:
                    print(f"[{idx+1}/{max_results}] Processing...", end=" ")
                    
                    # Scroll to make sure the element is in view
                    self.driver.execute_script(
                        "arguments[0].scrollTo(0, arguments[1]);", 
                        results_panel,
                        idx * 180  # Approximate height per listing
                    )
                    time.sleep(0.5)
                    
                    # Re-find elements each time to avoid stale references
                    listing_links = self.driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] > div > div > a")
                    
                    if idx >= len(listing_links):
                        print(f"✗ No more results available")
                        break
                    
                    # Click on the listing to open details panel
                    self.driver.execute_script("arguments[0].click();", listing_links[idx])
                    time.sleep(random.uniform(2.5, 3.5))
                    
                    # Extract business details
                    business_data = self._extract_business_details()
                    
                    if business_data:
                        self.results.append(business_data)
                        print(f"✓ {business_data['name']}")
                    else:
                        print("✗ Failed to extract")
                    
                    # Random delay to appear human-like
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    print(f"✗ Error: {str(e)[:50]}")
                    continue
                    
        except Exception as e:
            print(f"ERROR extracting listings: {e}")
    
    def _extract_business_details(self):
        """Extract detailed information from the currently open business listing."""
        data = {
            'name': 'N/A',
            'category': 'N/A',
            'address': 'N/A',
            'phone': 'N/A',
            'website': 'N/A',
            'rating': 'N/A',
            'reviews': 'N/A',
            'hours': 'N/A',
            'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Business Name
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf")
                data['name'] = name_elem.text
            except NoSuchElementException:
                pass
            
            # Category
            try:
                category_elem = self.driver.find_element(By.CSS_SELECTOR, "button[jsaction*='category']")
                data['category'] = category_elem.text
            except NoSuchElementException:
                pass
            
            # Address
            try:
                address_elem = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']")
                data['address'] = address_elem.get_attribute('aria-label').replace('Address: ', '')
            except NoSuchElementException:
                pass
            
            # Phone
            try:
                phone_elem = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='phone']")
                data['phone'] = phone_elem.get_attribute('aria-label').replace('Phone: ', '')
            except NoSuchElementException:
                pass
            
            # Website
            try:
                website_elem = self.driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
                data['website'] = website_elem.get_attribute('href')
            except NoSuchElementException:
                pass
            
            # Rating and Reviews
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "div.F7nice span[aria-hidden='true']")
                data['rating'] = rating_elem.text
                
                reviews_elem = self.driver.find_element(By.CSS_SELECTOR, "div.F7nice span[aria-label*='reviews']")
                data['reviews'] = reviews_elem.get_attribute('aria-label').split()[0]
            except NoSuchElementException:
                pass
            
            # Hours
            try:
                hours_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='oh']")
                data['hours'] = hours_button.get_attribute('aria-label')
            except NoSuchElementException:
                pass
            
        except Exception as e:
            print(f"Error extracting details: {e}")
        
        return data if data['name'] != 'N/A' else None
    
    def save_to_text(self, output_path):
        """Save results to a formatted text file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("GOOGLE MY BUSINESS LEAD GENERATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Leads: {len(self.results)}\n")
            f.write("=" * 80 + "\n\n")
            
            for idx, business in enumerate(self.results, 1):
                f.write(f"LEAD #{idx}\n")
                f.write("-" * 80 + "\n")
                f.write(f"Business Name:    {business['name']}\n")
                f.write(f"Category:         {business['category']}\n")
                f.write(f"Address:          {business['address']}\n")
                f.write(f"Phone:            {business['phone']}\n")
                f.write(f"Website:          {business['website']}\n")
                f.write(f"Rating:           {business['rating']} ({business['reviews']} reviews)\n")
                f.write(f"Hours:            {business['hours']}\n")
                f.write(f"Extracted:        {business['extracted_at']}\n")
                f.write("-" * 80 + "\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
        
        print(f"\n✅ Results saved to: {output_file}")
        print(f"📊 Total leads extracted: {len(self.results)}")
    
    def close(self):
        """Close the browser and clean up."""
        if self.driver:
            self.driver.quit()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Scrape Google My Business listings for lead generation'
    )
    parser.add_argument(
        'query',
        type=str,
        help='Search query (e.g., "restaurants in New York")'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=20,
        help='Maximum number of results to scrape (default: 20)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='.tmp/gmb_leads.txt',
        help='Output file path (default: .tmp/gmb_leads.txt)'
    )
    parser.add_argument(
        '--visible',
        action='store_true',
        help='Run browser in visible mode (not headless)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("🚀 GOOGLE MY BUSINESS LEAD SCRAPER")
    print("=" * 80)
    
    scraper = None
    try:
        # Initialize scraper
        scraper = GMBScraper(headless=not args.visible)
        
        # Perform search and extraction
        scraper.search(args.query, args.max_results)
        
        # Save results
        if scraper.results:
            scraper.save_to_text(args.output)
        else:
            print("\n⚠️  No results found. Try a different search query.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper:
            scraper.close()
        print("\n✨ Done!\n")


if __name__ == "__main__":
    main()
