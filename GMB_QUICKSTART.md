# GMB Lead Generation - Quick Start Guide

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r execution/requirements.txt
```

### 2. Install ChromeDriver

**macOS:**
```bash
brew install chromedriver
```

**Linux:**
```bash
# Download from https://chromedriver.chromium.org/
# Or use: sudo apt-get install chromium-chromedriver
```

**Windows:**
Download from https://chromedriver.chromium.org/ and add to PATH

## 📖 Usage

### Basic Usage

```bash
python execution/scrape_gmb_leads.py "restaurants in New York"
```

### Advanced Options

```bash
# Scrape 50 results
python execution/scrape_gmb_leads.py "plumbers in Austin TX" --max-results 50

# Custom output location
python execution/scrape_gmb_leads.py "dentists in Miami" --output leads/miami_dentists.txt

# Run with visible browser (for debugging)
python execution/scrape_gmb_leads.py "coffee shops in Seattle" --visible
```

### Full Command Reference

```bash
python execution/scrape_gmb_leads.py [QUERY] [OPTIONS]

Arguments:
  QUERY                 Search query (e.g., "restaurants in New York")

Options:
  --max-results N       Maximum number of results (default: 20)
  --output PATH         Output file path (default: .tmp/gmb_leads.txt)
  --visible             Run browser in visible mode (not headless)
  -h, --help           Show help message
```

## 📊 Output Format

Results are saved as a formatted text file with the following information for each lead:

- Business Name
- Category
- Address
- Phone Number
- Website
- Rating & Review Count
- Hours of Operation
- Extraction Timestamp

Example output location: `.tmp/gmb_leads.txt`

## 🎯 Example Queries

```bash
# Local services
python execution/scrape_gmb_leads.py "electricians in Boston"
python execution/scrape_gmb_leads.py "real estate agents in San Francisco"

# Retail
python execution/scrape_gmb_leads.py "pet stores in Chicago"
python execution/scrape_gmb_leads.py "bookstores in Portland OR"

# Food & Beverage
python execution/scrape_gmb_leads.py "italian restaurants in Manhattan"
python execution/scrape_gmb_leads.py "craft breweries in Denver"

# Professional Services
python execution/scrape_gmb_leads.py "law firms in Los Angeles"
python execution/scrape_gmb_leads.py "accounting firms in Dallas"
```

## ⚠️ Important Notes

### Rate Limiting
- The scraper includes random delays (2-5 seconds) between requests
- Recommended: Scrape during off-peak hours (2-6 AM local time)
- Don't exceed 100 results per session to avoid detection

### Legal Considerations
- Google's Terms of Service restrict automated scraping
- For production use, consider using the **Google Places API** (requires API key and billing)
- This tool is intended for personal research and testing only

### Troubleshooting

**"ChromeDriver not found"**
- Install ChromeDriver (see Setup section)
- Ensure it's in your PATH

**"No results found"**
- Try a more specific query
- Check your internet connection
- Google may be blocking automated requests (try --visible mode)

**Browser crashes or hangs**
- Reduce --max-results to a lower number
- Close other Chrome instances
- Restart your computer

## 🔄 Self-Annealing

If you encounter issues:
1. Check the error message
2. Update `execution/scrape_gmb_leads.py` with fixes
3. Test again
4. Document learnings in `directives/scrape_gmb_leads.md`

## 📈 Future Enhancements

- Email extraction from business websites
- Social media profile detection
- Lead scoring based on profile completeness
- Export to CSV/JSON formats
- CRM integration (Salesforce, HubSpot)
- Automated follow-up email generation
