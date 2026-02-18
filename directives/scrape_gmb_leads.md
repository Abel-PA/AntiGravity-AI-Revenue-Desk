# Scrape Google My Business Leads

## Goal
Extract business listing details from Google My Business (GMB) profiles to generate qualified leads. Output structured data in text format for easy review and processing.

## Inputs
- **Search Query**: Business type and location (e.g., "restaurants in New York", "plumbers in Austin TX")
- **Max Results**: Number of businesses to scrape (default: 20)
- **Output Path**: Location to save the text file (default: `.tmp/gmb_leads.txt`)

## Tools/Scripts
- `execution/scrape_gmb_leads.py` - Main scraping engine that extracts GMB profile data

## Outputs
- **Text File**: Structured text file containing:
  - Business Name
  - Address
  - Phone Number
  - Website
  - Rating & Review Count
  - Business Category
  - Hours of Operation
  - Additional metadata (if available)

## Process Flow
1. Accept search query and parameters
2. Search Google Maps for matching businesses
3. Extract detailed information from each listing
4. Format data in readable text format
5. Save to output file
6. Display summary statistics

## Edge Cases
- **Rate Limiting**: Google may block rapid requests
  - Solution: Add random delays between requests (2-5 seconds)
  - Use rotating user agents
  
- **CAPTCHA Detection**: Google may present CAPTCHAs
  - Solution: Implement detection and graceful failure
  - Option to use browser automation (Selenium) for human-like behavior

- **Missing Data**: Not all fields available for every business
  - Solution: Mark missing fields as "N/A"
  - Continue processing even with partial data

- **Pagination**: Results may span multiple pages
  - Solution: Implement scroll/pagination handling
  - Respect max_results parameter

- **Dynamic Content**: GMB uses JavaScript rendering
  - Solution: Use Selenium WebDriver for full page rendering
  - Alternative: Use Google Places API (requires API key)

## Notes
- Google's Terms of Service restrict automated scraping
- Consider using Google Places API for production use (requires billing)
- For testing/personal use, implement respectful scraping:
  - Random delays between requests
  - Limit concurrent requests
  - Use during off-peak hours
- Browser automation (Selenium) is more reliable than raw HTTP requests
- Data quality varies by business (some have incomplete profiles)
- **LEARNING (2026-02-11)**: Visible mode (`--visible` flag) is significantly more reliable than headless mode
  - Headless mode encounters "stale element reference" errors frequently
  - Visible mode successfully extracts all requested leads
  - Recommend using `--visible` for production scraping until headless issues are resolved
- Successfully tested with Harrisburg, PA leads (HVAC, Roofers, Plumbers)
- Average extraction time: ~5-6 seconds per lead
- Typical success rate: 100% in visible mode, ~10% in headless mode

## Future Improvements
- Add email extraction from websites
- Social media profile detection
- Lead scoring based on profile completeness
- Export to CSV/JSON formats
- Integration with CRM systems
