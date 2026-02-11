# RFP-Gathering

A tool to aggregate Request for Proposals (RFPs) from government websites and save the information to a viewable file.

## Features

- Aggregates RFPs from the Indiana Department of Administration (IDOA) procurement website
- Uses web scraping with BeautifulSoup to extract RFP data
- Saves RFP information in JSON format for easy viewing
- Displays a summary of collected RFPs
- Configurable via `config.json`
- Includes proper error handling for network requests

## Installation

1. Clone this repository:
```bash
git clone https://github.com/mccreamatthewj/RFP-Gathering.git
cd RFP-Gathering
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the RFP gathering tool:

```bash
python rfp_gatherer.py
```

The tool will:
1. Gather RFPs from the Indiana IDOA procurement website
2. Display a summary in the terminal
3. Save all RFP data to `rfp_data.json`

## Output Format

The RFP data is saved in JSON format with the following structure:

```json
{
  "collected_at": "2024-02-11T12:00:00",
  "total_rfps": 3,
  "rfps": [
    {
      "title": "Technology Services for State Systems",
      "agency": "Indiana Department of Administration",
      "posted_date": "2024-02-01",
      "due_date": "2024-03-15",
      "notice_id": "IN-IDOA-001-2024",
      "description": "Request for proposals for technology services and systems integration",
      "source": "Indiana IDOA",
      "url": "https://www.in.gov/idoa/procurement/current-business-opportunities/"
    }
  ]
}
```

## Configuration

Edit `config.json` to customize:
- Government websites to scrape
- Output file name
- Search keywords

## Viewing the Data

After running the tool, you can view the RFP data in several ways:

1. **JSON file**: Open `rfp_data.json` in any text editor
2. **Command line**: Use `cat rfp_data.json | python -m json.tool` for formatted output
3. **Terminal summary**: The tool displays a summary when run

## Note

This tool scrapes the Indiana Department of Administration's procurement website to gather current business opportunities. The scraper:
- Uses BeautifulSoup to parse HTML content
- Includes user-agent headers to avoid being blocked
- Has error handling for network issues
- Falls back to sample data if the website cannot be accessed

For production use, ensure compliance with the website's terms of service and implement appropriate rate limiting.

## License

MIT