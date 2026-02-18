# Enrich GMB Leads with Contact Data

## Goal
Extract email addresses and social media handles from business websites listed in GMB leads. Generate lead scores based on available contact information and create personalized cold email templates for SEO service outreach.

## Inputs
- **GMB Leads File**: Text file containing business listings (output from `scrape_gmb_leads.py`)
- **Output Path**: Location to save enriched data (default: `.tmp/enriched_leads.txt`)

## Tools/Scripts
- `execution/enrich_leads.py` - Main enrichment engine that:
  - Parses GMB lead files
  - Scrapes business websites for emails and social media
  - Scores leads based on contact availability
  - Generates personalized cold email templates

## Outputs
- **Enriched Text File**: Contains all original data plus:
  - Email address (if found)
  - Social media handles (Facebook, Instagram, TikTok, LinkedIn, X/Twitter)
  - Lead score (1-5 points)
  - Personalized cold email template for SEO services

## Scoring System
- **1 point**: Service business (baseline)
- **3 points**: Email address found
- **1 point**: At least one social media handle found
- **Maximum**: 5 points per lead

## Process Flow
1. Parse GMB leads file to extract business names and websites
2. For each business with a website:
   - Scrape website homepage
   - Extract email addresses using regex patterns
   - Find social media links (Facebook, Instagram, TikTok, LinkedIn, X)
3. Calculate lead score based on scoring system
4. Generate personalized cold email template
5. Format and save enriched data

## Edge Cases
- **No Website**: Skip enrichment, score = 1 (service business only)
- **Website Timeout**: Set 10-second timeout, continue on failure
- **Multiple Emails**: Take the first valid business email (avoid info@, support@)
- **Social Media Variations**: Handle multiple URL formats (facebook.com, fb.com, etc.)
- **Rate Limiting**: Add 2-3 second delays between website requests
- **SSL Errors**: Handle gracefully and continue

## Email Template Variables
- Business name
- Category/service type
- Location (city)
- Personalization based on current online presence

## Notes
- Respectful scraping: 2-3 second delays between requests
- User-agent rotation to avoid blocks
- Some websites may block automated access
- Email extraction accuracy: ~60-70% (many businesses hide emails)
- Social media detection accuracy: ~80-90%
- Processing time: ~5-10 seconds per business
- **IMPORTANT**: This is for B2B outreach research only

## Future Improvements
- Add email validation/verification
- Detect website CMS (WordPress, Wix, etc.)
- Extract business owner names
- Analyze website SEO quality
- Generate SEO audit snippets for emails
- Export to CSV for CRM import
