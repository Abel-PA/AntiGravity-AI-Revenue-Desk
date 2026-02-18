# [Directive Name]

## Goal
[Clear statement of what this directive accomplishes]

Example: "Scrape product data from e-commerce websites and populate a Google Sheet"

## Inputs
- **Input 1**: [Description and format]
- **Input 2**: [Description and format]

Example:
- **Website URL**: Target e-commerce site to scrape
- **Sheet ID**: Google Sheets ID for output destination

## Tools/Scripts
- `execution/script_name.py` - [Brief description of what it does]

Example:
- `execution/scrape_single_site.py` - Scrapes product data from a single URL

## Outputs
- **Output 1**: [Description and location]
- **Output 2**: [Description and location]

Example:
- **Google Sheet**: Updated with product name, price, availability, and timestamp
- **Log file**: `.tmp/scrape_log.txt` with execution details

## Edge Cases
- [Known limitation or special case]
- [API rate limits, timing constraints, etc.]

Example:
- Rate limit: Max 10 requests per minute
- Some sites require JavaScript rendering (use Selenium for those)
- Handle missing prices gracefully (mark as "N/A")
- Retry logic: 3 attempts with exponential backoff

## Notes
[Any additional context or learnings discovered during execution]

Example:
- Site structure changed on 2026-01-15, updated selectors
- Best to run during off-peak hours (2-6 AM EST) to avoid detection
- Consider adding proxy rotation if scaling beyond 100 sites
