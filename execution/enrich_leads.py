#!/usr/bin/env python3
"""
Lead Enrichment Engine
Extracts email addresses and social media handles from business websites.
Generates lead scores and personalized cold email templates.
"""

import argparse
import re
import time
import random
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Run: pip install requests beautifulsoup4")
    sys.exit(1)


class LeadEnricher:
    """Enriches business leads with contact data from websites."""
    
    def __init__(self):
        """Initialize the enricher."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.enriched_leads = []
        
    def parse_gmb_file(self, filepath):
        """Parse GMB leads file and extract business data."""
        leads = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by lead sections
        lead_sections = re.split(r'LEAD #\d+\n-+', content)
        
        for section in lead_sections[1:]:  # Skip header
            lead = {}
            
            # Extract fields
            name_match = re.search(r'Business Name:\s+(.+)', section)
            category_match = re.search(r'Category:\s+(.+)', section)
            address_match = re.search(r'Address:\s+(.+)', section)
            phone_match = re.search(r'Phone:\s+(.+)', section)
            website_match = re.search(r'Website:\s+(.+)', section)
            rating_match = re.search(r'Rating:\s+(.+)', section)
            
            if name_match:
                lead['name'] = name_match.group(1).strip()
                lead['category'] = category_match.group(1).strip() if category_match else 'N/A'
                lead['address'] = address_match.group(1).strip() if address_match else 'N/A'
                lead['phone'] = phone_match.group(1).strip() if phone_match else 'N/A'
                lead['website'] = website_match.group(1).strip() if website_match else 'N/A'
                lead['rating'] = rating_match.group(1).strip() if rating_match else 'N/A'
                
                # Extract city from address
                if lead['address'] != 'N/A':
                    city_match = re.search(r',\s*([^,]+),\s*[A-Z]{2}', lead['address'])
                    lead['city'] = city_match.group(1) if city_match else 'your area'
                else:
                    lead['city'] = 'your area'
                
                leads.append(lead)
        
        return leads
    
    def clean_website_url(self, url):
        """Clean and normalize website URL."""
        if url == 'N/A' or not url:
            return None
        
        # Remove UTM parameters and other tracking
        url = re.sub(r'\?.*$', '', url)
        
        # Ensure it has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def extract_emails(self, html, url):
        """Extract email addresses from HTML content."""
        emails = set()
        
        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Find all emails in HTML
        found_emails = re.findall(email_pattern, html)
        
        # Filter out common generic emails and images
        generic_prefixes = ['info', 'support', 'hello', 'contact', 'admin', 'webmaster', 
                           'noreply', 'no-reply', 'sales', 'marketing']
        
        for email in found_emails:
            email_lower = email.lower()
            
            # Skip image files and generic emails
            if email_lower.endswith(('.png', '.jpg', '.gif', '.jpeg')):
                continue
            
            prefix = email_lower.split('@')[0]
            
            # Prefer specific emails over generic ones
            if not any(gen in prefix for gen in generic_prefixes):
                emails.add(email)
        
        # If no specific emails found, use generic ones
        if not emails:
            for email in found_emails:
                if not email.lower().endswith(('.png', '.jpg', '.gif', '.jpeg')):
                    emails.add(email)
                    break
        
        return list(emails)[:1]  # Return first email only
    
    def extract_social_media(self, html, base_url):
        """Extract social media handles from HTML content."""
        social = {
            'facebook': None,
            'instagram': None,
            'tiktok': None,
            'linkedin': None,
            'twitter': None
        }
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href'].lower()
            
            # Facebook
            if 'facebook.com' in href or 'fb.com' in href or 'fb.me' in href:
                handle = re.search(r'(?:facebook\.com|fb\.com|fb\.me)/([^/?]+)', href)
                if handle and not social['facebook']:
                    social['facebook'] = f"facebook.com/{handle.group(1)}"
            
            # Instagram
            elif 'instagram.com' in href:
                handle = re.search(r'instagram\.com/([^/?]+)', href)
                if handle and not social['instagram']:
                    social['instagram'] = f"instagram.com/{handle.group(1)}"
            
            # TikTok
            elif 'tiktok.com' in href:
                handle = re.search(r'tiktok\.com/@?([^/?]+)', href)
                if handle and not social['tiktok']:
                    social['tiktok'] = f"tiktok.com/@{handle.group(1)}"
            
            # LinkedIn
            elif 'linkedin.com' in href:
                handle = re.search(r'linkedin\.com/(?:company|in)/([^/?]+)', href)
                if handle and not social['linkedin']:
                    social['linkedin'] = f"linkedin.com/company/{handle.group(1)}"
            
            # Twitter/X
            elif 'twitter.com' in href or 'x.com' in href:
                handle = re.search(r'(?:twitter\.com|x\.com)/([^/?]+)', href)
                if handle and not social['twitter']:
                    social['twitter'] = f"x.com/{handle.group(1)}"
        
        return social
    
    def scrape_website(self, url):
        """Scrape website for email and social media."""
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            html = response.text
            
            # Extract emails and social media
            emails = self.extract_emails(html, url)
            social = self.extract_social_media(html, url)
            
            return {
                'email': emails[0] if emails else None,
                'social': social
            }
            
        except Exception as e:
            print(f"  ⚠️  Error scraping website: {str(e)[:50]}")
            return {
                'email': None,
                'social': {
                    'facebook': None,
                    'instagram': None,
                    'tiktok': None,
                    'linkedin': None,
                    'twitter': None
                }
            }
    
    def calculate_score(self, lead_data):
        """Calculate lead score based on available contact info."""
        score = 1  # Base score for service business
        
        # +3 points for email
        if lead_data.get('email'):
            score += 3
        
        # +1 point for at least one social media handle
        social = lead_data.get('social', {})
        if any(social.values()):
            score += 1
        
        return score
    
    def generate_cold_email(self, lead):
        """Generate personalized cold email template for SEO services."""
        name = lead['name']
        category = lead['category']
        city = lead['city']
        has_email = lead.get('email') is not None
        social_count = sum(1 for v in lead.get('social', {}).values() if v)
        
        # Personalization based on online presence
        if has_email and social_count >= 2:
            presence = "strong online presence"
        elif has_email or social_count >= 1:
            presence = "growing online presence"
        else:
            presence = "opportunity to expand your digital footprint"
        
        email_template = f"""
Subject: Help {name} Rank #1 in {city} for {category}

Hi [Owner/Manager Name],

I came across {name} while researching top {category.lower()} businesses in {city}, and I was impressed by your {lead['rating']} rating!

I noticed you have a {presence}, and I wanted to reach out because I specialize in helping local service businesses like yours dominate Google search results.

Here's what I can help you achieve:

✅ Rank #1 for "{category} in {city}" and related searches
✅ Generate 10-20+ qualified leads per month from Google
✅ Outrank your competitors in local search results
✅ Optimize your Google Business Profile for maximum visibility

I'd love to offer you a FREE SEO audit (worth $500) that will show you:
• Exactly where you rank vs. competitors
• Quick wins to get more leads this month
• A custom roadmap to dominate your local market

Would you be open to a quick 15-minute call this week to discuss how we can grow {name}?

Best regards,
[Your Name]
[Your Company]
[Your Phone]
[Your Email]

P.S. I'm only taking on 3 new clients this month, so if you're interested, let me know ASAP!
"""
        
        return email_template.strip()
    
    def enrich_leads(self, leads):
        """Enrich all leads with contact data."""
        print(f"\n🔍 Enriching {len(leads)} leads...\n")
        
        for idx, lead in enumerate(leads, 1):
            print(f"[{idx}/{len(leads)}] {lead['name'][:40]}...", end=" ")
            
            # Clean website URL
            website = self.clean_website_url(lead['website'])
            
            if website:
                # Scrape website
                contact_data = self.scrape_website(website)
                lead['email'] = contact_data['email']
                lead['social'] = contact_data['social']
                
                # Random delay
                time.sleep(random.uniform(2, 3))
            else:
                lead['email'] = None
                lead['social'] = {
                    'facebook': None,
                    'instagram': None,
                    'tiktok': None,
                    'linkedin': None,
                    'twitter': None
                }
            
            # Calculate score
            lead['score'] = self.calculate_score(lead)
            
            # Generate cold email
            lead['cold_email'] = self.generate_cold_email(lead)
            
            # Status
            status = f"✓ Score: {lead['score']}/5"
            if lead['email']:
                status += f" | Email: ✓"
            social_count = sum(1 for v in lead['social'].values() if v)
            if social_count > 0:
                status += f" | Social: {social_count}"
            
            print(status)
            
            self.enriched_leads.append(lead)
        
        print(f"\n✅ Enrichment complete!")
    
    def save_to_text(self, output_path):
        """Save enriched leads to text file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Sort by score (highest first)
        sorted_leads = sorted(self.enriched_leads, key=lambda x: x['score'], reverse=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ENRICHED LEAD GENERATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Leads: {len(sorted_leads)}\n")
            f.write(f"Average Score: {sum(l['score'] for l in sorted_leads) / len(sorted_leads):.1f}/5.0\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary statistics
            with_email = sum(1 for l in sorted_leads if l['email'])
            with_social = sum(1 for l in sorted_leads if any(l['social'].values()))
            
            f.write("📊 SUMMARY STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Leads with Email: {with_email} ({with_email/len(sorted_leads)*100:.0f}%)\n")
            f.write(f"Leads with Social Media: {with_social} ({with_social/len(sorted_leads)*100:.0f}%)\n")
            f.write(f"High-Value Leads (4-5 points): {sum(1 for l in sorted_leads if l['score'] >= 4)}\n")
            f.write("\n" + "=" * 80 + "\n\n")
            
            for idx, lead in enumerate(sorted_leads, 1):
                f.write(f"LEAD #{idx} - SCORE: {lead['score']}/5 ⭐\n")
                f.write("-" * 80 + "\n")
                f.write(f"Business Name:    {lead['name']}\n")
                f.write(f"Category:         {lead['category']}\n")
                f.write(f"Address:          {lead['address']}\n")
                f.write(f"Phone:            {lead['phone']}\n")
                f.write(f"Website:          {lead['website']}\n")
                f.write(f"Rating:           {lead['rating']}\n")
                f.write(f"\n📧 CONTACT INFORMATION:\n")
                f.write(f"Email:            {lead['email'] if lead['email'] else 'Not found'}\n")
                f.write(f"Facebook:         {lead['social']['facebook'] if lead['social']['facebook'] else 'Not found'}\n")
                f.write(f"Instagram:        {lead['social']['instagram'] if lead['social']['instagram'] else 'Not found'}\n")
                f.write(f"TikTok:           {lead['social']['tiktok'] if lead['social']['tiktok'] else 'Not found'}\n")
                f.write(f"LinkedIn:         {lead['social']['linkedin'] if lead['social']['linkedin'] else 'Not found'}\n")
                f.write(f"Twitter/X:        {lead['social']['twitter'] if lead['social']['twitter'] else 'Not found'}\n")
                f.write(f"\n💌 COLD EMAIL TEMPLATE:\n")
                f.write("-" * 80 + "\n")
                f.write(lead['cold_email'])
                f.write("\n" + "-" * 80 + "\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
        
        print(f"\n✅ Results saved to: {output_file}")
        print(f"📊 Total leads enriched: {len(sorted_leads)}")
        print(f"📧 Emails found: {with_email}")
        print(f"📱 Social media found: {with_social}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Enrich GMB leads with email and social media data'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Input GMB leads file (e.g., .tmp/harrisburg_hvac.txt)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: input_file with _enriched suffix)'
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input_file)
        output_path = input_path.parent / f"{input_path.stem}_enriched.txt"
    
    print("\n" + "=" * 80)
    print("🚀 LEAD ENRICHMENT ENGINE")
    print("=" * 80)
    
    try:
        enricher = LeadEnricher()
        
        # Parse GMB file
        print(f"\n📖 Reading leads from: {args.input_file}")
        leads = enricher.parse_gmb_file(args.input_file)
        print(f"✅ Found {len(leads)} leads")
        
        # Enrich leads
        enricher.enrich_leads(leads)
        
        # Save results
        enricher.save_to_text(output_path)
        
    except FileNotFoundError:
        print(f"\n❌ ERROR: File not found: {args.input_file}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✨ Done!\n")


if __name__ == "__main__":
    main()
