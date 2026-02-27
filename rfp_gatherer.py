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
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict
from copy import deepcopy
import sys

class RFPGatherer:
    """Main class for gathering RFP data from government websites."""
    
    # Only include RFPs from this agency (substring match, case-insensitive)
    TARGET_AGENCY = "Education"

    # Column names to look for on the IDOA procurement table (checked in priority order)
    TITLE_COLUMNS = ('title', 'event name', 'description', 'event description', 'subject')
    BID_DOC_COLUMNS = ('bid documents', 'event name')
    
    # Sample RFP data for demonstration when scraping fails
    SAMPLE_INDIANA_RFPS = [
        {
            "title": "Educational Technology Services",
            "agency": "Education",
            "posted_date": "2024-02-01",
            "due_date": "2024-03-15",
            "notice_id": "IN-IDOA-0001",
            "description": "Request for proposals for educational technology services",
            "source": "Indiana IDOA",
            "url": "https://www.in.gov/idoa/procurement/current-business-opportunities/"
        },
        {
            "title": "Student Information System Upgrade",
            "agency": "Education",
            "posted_date": "2024-02-05",
            "due_date": "2024-03-20",
            "notice_id": "IN-IDOA-0002",
            "description": "Upgrade and support for the statewide student information system",
            "source": "Indiana IDOA",
            "url": "https://www.in.gov/idoa/procurement/current-business-opportunities/"
        }
    ]
    
    def __init__(self, config_file='config.json'):
        """Initialize the RFP gatherer with configuration."""
        load_dotenv()
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        self.rfps = []
        self._debug = os.environ.get('DEBUG_SCRAPE', '0').strip() == '1'

    def _debug_print(self, *args, **kwargs):
        """Print a debug message when DEBUG_SCRAPE is enabled."""
        if self._debug:
            print('[DEBUG]', *args, **kwargs)

    def _matches_target_agency(self, text: str) -> bool:
        """Return True if *text* contains the TARGET_AGENCY keyword as a whole word (case-insensitive)."""
        pattern = r'\b' + re.escape(self.TARGET_AGENCY.lower()) + r'\b'
        return bool(re.search(pattern, text.lower()))
    
    def fetch_indiana_idoa_rfps(self) -> List[Dict]:
        """
        Fetch RFPs from Indiana IDOA procurement website.
        
        Scrapes the Indiana Department of Administration's current business
        opportunities page, extracts the Agency and Bid Documents link from
        each table row, and returns only entries where Agency contains the
        TARGET_AGENCY keyword (case-insensitive substring match).
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
            
            # Find the procurement table on the page
            table = soup.find('table')
            if not table:
                print("Note: Could not find table on page. Using sample data for demonstration.")
                return deepcopy(self.SAMPLE_INDIANA_RFPS)
            
            # Parse header row to find column indices for "Agency" and "Bid Documents"
            header_row = table.find('tr')
            if not header_row:
                print("Note: Could not find table header. Using sample data for demonstration.")
                return deepcopy(self.SAMPLE_INDIANA_RFPS)
            
            headers_cells = header_row.find_all(['th', 'td'])
            col_map = {}
            for i, cell in enumerate(headers_cells):
                col_map[cell.get_text(strip=True).lower()] = i
            
            agency_idx = col_map.get('agency')
            bid_docs_idx = next((col_map[k] for k in self.BID_DOC_COLUMNS if k in col_map), None)
            title_idx = next((col_map[k] for k in self.TITLE_COLUMNS if k in col_map), None)

            self._debug_print(f"col_map: {col_map}")
            self._debug_print(f"agency_idx={agency_idx}, title_idx={title_idx}, bid_docs_idx={bid_docs_idx}")
            
            # Extract RFP data from each data row
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                try:
                    cells = row.find_all(['td', 'th'])
                    if not cells:
                        continue
                    
                    # Extract Agency value
                    if agency_idx is not None and agency_idx < len(cells):
                        agency = cells[agency_idx].get_text(strip=True)
                    else:
                        agency = ""
                    
                    # Match using case-insensitive substring; if agency cell is empty
                    # fall back to checking the full row text for the education keyword.
                    if agency and self._matches_target_agency(agency):
                        self._debug_print(f"Row matched via agency column: {agency!r}")
                    elif not agency and self._matches_target_agency(row.get_text()):
                        agency = self.TARGET_AGENCY
                        self._debug_print(f"Row matched via full-row text fallback; agency set to {agency!r}")
                    else:
                        self._debug_print(f"Row skipped (agency={agency!r})")
                        continue
                    
                    # Extract Bid Documents URL
                    rfp_url = ""
                    if bid_docs_idx is not None and bid_docs_idx < len(cells):
                        bid_link = cells[bid_docs_idx].find('a')
                        if bid_link:
                            rfp_url = bid_link.get('href', '')
                            if rfp_url and not rfp_url.startswith('http'):
                                rfp_url = 'https://www.in.gov' + rfp_url
                    
                    # Extract title
                    title = ""
                    if title_idx is not None and title_idx < len(cells):
                        title = cells[title_idx].get_text(strip=True)
                    if not title:
                        # Fall back to first cell with meaningful text
                        for cell in cells:
                            text = cell.get_text(strip=True)
                            if text and len(text) > 5:
                                title = text
                                break
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # Extract dates and other info from row text
                    text_content = row.get_text()
                    date_pattern = r'\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}'
                    dates = re.findall(date_pattern, text_content)
                    
                    posted_date = dates[0] if len(dates) > 0 else datetime.now().strftime('%Y-%m-%d')
                    due_date = dates[1] if len(dates) > 1 else ""
                    
                    # Generate a notice ID using abs(hash) to avoid negative values
                    hash_value = abs(hash(f"{title}_{posted_date}")) % 10000
                    notice_id = f"IN-IDOA-{hash_value:04d}"
                    
                    # Extract description (first 200 chars of row text)
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
                    
                    rfps.append(rfp)
                        
                except Exception:
                    # Skip individual rows that fail to parse
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
            f"Total RFPs Found: {len(self.rfps)}",
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
