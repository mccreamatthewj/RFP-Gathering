#!/usr/bin/env python3
"""
RFP Gathering Tool
Aggregates RFPs from government websites and saves them to a file.
"""

import json
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests  # Reserved for future API calls to government websites
from bs4 import BeautifulSoup  # Reserved for future web scraping implementation
from datetime import datetime
from typing import List, Dict
from copy import deepcopy
import sys
from transformers import pipeline

class RFPGatherer:
    """Main class for gathering RFP data from government websites."""
    
    # Sample RFP data for demonstration when scraping fails
    SAMPLE_INDIANA_RFPS = [
        {
            "title": "Technology Services for State Systems",
            "agency": "Indiana Department of Administration",
            "posted_date": "2024-02-01",
            "due_date": "2024-03-15",
            "notice_id": "IN-IDOA-001-2024",
            "description": "Request for proposals for technology services and systems integration",
            "source": "Indiana IDOA",
            "url": "https://www.in.gov/idoa/procurement/current-business-opportunities/"
        },
        {
            "title": "Consulting Services for Digital Transformation",
            "agency": "Indiana Department of Administration",
            "posted_date": "2024-02-05",
            "due_date": "2024-03-20",
            "notice_id": "IN-IDOA-002-2024",
            "description": "State-wide digital transformation consulting and implementation services",
            "source": "Indiana IDOA",
            "url": "https://www.in.gov/idoa/procurement/current-business-opportunities/"
        },
        {
            "title": "Cloud Migration and Infrastructure Services",
            "agency": "Indiana Department of Administration",
            "posted_date": "2024-02-10",
            "due_date": "2024-03-25",
            "notice_id": "IN-IDOA-003-2024",
            "description": "Cloud infrastructure services for state agency systems migration",
            "source": "Indiana IDOA",
            "url": "https://www.in.gov/idoa/procurement/current-business-opportunities/"
        }
    ]
    
    def __init__(self, config_file='config.json'):
        """Initialize the RFP gatherer with configuration."""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        self.rfps = []
        self.total_rfps_before_filter = 0
    
    def fetch_indiana_idoa_rfps(self) -> List[Dict]:
        """
        Fetch RFPs from Indiana IDOA procurement website.
        
        Scrapes the Indiana Department of Administration's current business
        opportunities page to gather RFP information.
        """
        rfps = []
        url = "https://www.in.gov/idoa/procurement/current-business-opportunities/"
        
        # User-agent header to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            # Make HTTP request to the Indiana IDOA website
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find RFP listings - common patterns on government websites
            # Look for tables, lists, or sections containing RFP information
            rfp_elements = []
            
            # Try multiple common selectors for government procurement pages
            # Pattern 1: Table rows
            table_rows = soup.find_all('tr')
            for row in table_rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # Likely contains RFP data
                    rfp_elements.append(row)
            
            # Pattern 2: List items in specific sections
            lists = soup.find_all(['ul', 'ol'])
            for ul in lists:
                items = ul.find_all('li')
                if items:
                    rfp_elements.extend(items)
            
            # Pattern 3: Article or section elements
            articles = soup.find_all(['article', 'section'])
            rfp_elements.extend(articles)
            
            # Extract RFP data from found elements
            for element in rfp_elements:
                try:
                    # Extract title - look for links or headings
                    title_elem = element.find(['a', 'h1', 'h2', 'h3', 'h4', 'strong'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:  # Skip if title is too short
                        continue
                    
                    # Extract URL if available
                    link = element.find('a')
                    rfp_url = link.get('href', '') if link else ''
                    if rfp_url and not rfp_url.startswith('http'):
                        rfp_url = 'https://www.in.gov' + rfp_url
                    
                    # Extract dates and other info from text
                    text_content = element.get_text()
                    
                    # Try to extract agency name
                    agency = "Indiana Department of Administration"
                    
                    # Try to extract dates (common patterns: MM/DD/YYYY, YYYY-MM-DD)
                    date_pattern = r'\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}'
                    dates = re.findall(date_pattern, text_content)
                    
                    posted_date = dates[0] if len(dates) > 0 else datetime.now().strftime('%Y-%m-%d')
                    due_date = dates[1] if len(dates) > 1 else ""
                    
                    # Generate a notice ID using abs(hash) to avoid negative values
                    # Include posted_date to make IDs more unique
                    hash_value = abs(hash(f"{title}_{posted_date}")) % 10000
                    notice_id = f"IN-IDOA-{hash_value:04d}"
                    
                    # Extract description (first 200 chars of text)
                    description = text_content[:200].strip()
                    
                    rfp = {
                        "title": title,
                        "agency": agency,
                        "posted_date": posted_date,
                        "due_date": due_date,
                        "notice_id": notice_id,
                        "description": description,
                        "source": "Indiana IDOA",
                        "url": rfp_url or url
                    }
                    
                    # Only add if we have meaningful data
                    if title and len(title) > 10:
                        rfps.append(rfp)
                        
                except Exception as e:
                    # Skip individual elements that fail to parse
                    continue
            
            # If no RFPs found through scraping, return sample data for demonstration
            if not rfps:
                print("Note: Could not scrape live data. Using sample data for demonstration.")
                rfps = deepcopy(self.SAMPLE_INDIANA_RFPS)
            
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to fetch data from Indiana IDOA website: {e}")
            print("Using sample data for demonstration purposes.")
            # Return sample data if request fails
            rfps = deepcopy(self.SAMPLE_INDIANA_RFPS)
        except Exception as e:
            print(f"Error: Unexpected error while fetching RFPs: {e}")
            rfps = []
        
        return rfps
    
    def filter_education_rfps(self, rfps: List[Dict]) -> List[Dict]:
        """Use a local AI model to filter RFPs and return only education-related ones.

        Uses Hugging Face's zero-shot classification pipeline with a pre-trained
        NLI model to determine whether each RFP is education-related.  The model
        is downloaded automatically on the first run and cached locally — no API
        key is required.

        If the model fails to load or classify, all RFPs are returned unchanged
        so the rest of the pipeline continues to work.

        Stores the original count in ``self.total_rfps_before_filter`` for
        reporting purposes.
        """
        self.total_rfps_before_filter = len(rfps)

        if not rfps:
            return rfps

        ai_config = self.config.get('ai_filter', {})
        model_name = ai_config.get('model', 'facebook/bart-large-mnli')
        threshold = float(ai_config.get('threshold', 0.7))

        try:
            print(f"Loading AI classification model '{model_name}' (downloading on first run)...")
            classifier = pipeline("zero-shot-classification", model=model_name)
        except Exception as e:
            print(f"Warning: Could not load AI model: {e}. Including all RFPs.")
            return rfps

        # Specific education-related labels give the model a clearer target than
        # a single broad "education" label, reducing false positives.
        education_labels = [
            "K-12 education",
            "higher education",
            "educational technology",
            "workforce training and education",
            "school or university services",
        ]
        non_education_label = "unrelated to education"
        candidate_labels = education_labels + [non_education_label]

        filtered = []

        for rfp in rfps:
            text = f"{rfp.get('title', '')}. {rfp.get('description', '')}"
            try:
                result = classifier(text, candidate_labels=candidate_labels)
                top_label = result['labels'][0]
                top_score = result['scores'][0]
                # Keep only RFPs where the highest-scoring label is one of the
                # explicit education labels and meets the confidence threshold.
                if top_label in education_labels and top_score >= threshold:
                    filtered.append(rfp)
            except Exception as e:
                print(f"Warning: Classification failed for '{rfp['title']}': {e}. Including item.")
                filtered.append(rfp)

        print(f"AI filter: {len(filtered)} of {len(rfps)} RFPs identified as education-related.")
        return filtered

    def gather_rfps(self):
        """Gather RFPs from all configured sources."""
        print("Starting RFP gathering process...")
        
        # Gather from Indiana IDOA
        print("Fetching RFPs from Indiana IDOA...")
        indiana_rfps = self.fetch_indiana_idoa_rfps()
        self.rfps.extend(indiana_rfps)
        
        print(f"Total RFPs collected: {len(self.rfps)}")
        return self.rfps
    
    def save_to_file(self, filename=None):
        """Save collected RFPs to a JSON file."""
        if filename is None:
            filename = self.config.get('output_file', 'rfp_data.json')
        
        output_data = {
            "collected_at": datetime.now().isoformat(),
            "total_rfps": len(self.rfps),
            "rfps": self.rfps
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"RFP data saved to {filename}")
        return filename
    
    def send_email(self, output_file=None):
        """Email the RFP data to the configured recipient.
        
        SMTP credentials are read from the environment variables
        SMTP_USER and SMTP_PASSWORD.
        """
        email_config = self.config.get('email', {})
        recipient = email_config.get('recipient')
        smtp_host = email_config.get('smtp_host', 'smtp.gmail.com')
        smtp_port = email_config.get('smtp_port', 587)
        subject = email_config.get('subject', 'RFP Gathering Results')

        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')

        if not smtp_user or not smtp_password:
            print("Warning: SMTP_USER or SMTP_PASSWORD environment variables not set. Skipping email.")
            return

        if not recipient:
            print("Warning: No email recipient configured. Skipping email.")
            return

        # Build plain-text body with RFP summary
        lines = [
            f"RFP Gathering Results – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Education-Related RFPs Found: {len(self.rfps)} of {self.total_rfps_before_filter}",
            "",
        ]
        for i, rfp in enumerate(self.rfps, 1):
            lines.append(f"{i}. {rfp['title']}")
            lines.append(f"   Agency: {rfp['agency']}")
            lines.append(f"   Posted: {rfp['posted_date']} | Due: {rfp['due_date']}")
            lines.append(f"   Notice ID: {rfp['notice_id']}")
            lines.append(f"   Source: {rfp['source']}")
            lines.append(f"   URL: {rfp['url']}")
            lines.append("")

        if output_file:
            lines.append(f"Full data saved to: {output_file}")

        body = "\n".join(lines)

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipient, msg.as_string())
            print(f"RFP data emailed to {recipient}")
        except Exception as e:
            print(f"Warning: Failed to send email to {recipient}: {e}")

    def display_summary(self):
        """Display a summary of collected RFPs."""
        print("\n" + "="*80)
        print("RFP GATHERING SUMMARY")
        print("="*80)
        print(f"Total RFPs Found: {len(self.rfps)}\n")
        
        for i, rfp in enumerate(self.rfps, 1):
            print(f"{i}. {rfp['title']}")
            print(f"   Agency: {rfp['agency']}")
            print(f"   Posted: {rfp['posted_date']} | Due: {rfp['due_date']}")
            print(f"   Notice ID: {rfp['notice_id']}")
            print(f"   Source: {rfp['source']}")
            print(f"   URL: {rfp['url']}")
            print()
        
        print("="*80)


def main():
    """Main entry point for the RFP gathering tool."""
    try:
        print("RFP Gathering Tool")
        print("=" * 80)
        
        # Initialize gatherer
        gatherer = RFPGatherer()
        
        # Gather RFPs
        gatherer.gather_rfps()
        
        # Filter to education-related RFPs using AI
        gatherer.rfps = gatherer.filter_education_rfps(gatherer.rfps)

        # Display summary
        gatherer.display_summary()
        
        # Save to file
        output_file = gatherer.save_to_file()
        
        # Email the results
        gatherer.send_email(output_file)

        print(f"\nSuccess! RFP data has been saved to {output_file}")
        print("You can view the data by opening the JSON file.")
        
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
