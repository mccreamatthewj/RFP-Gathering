# RFP-Gathering

A tool to aggregate Request for Proposals (RFPs) from government websites and save the information to a viewable file.

## Features

- Aggregates RFPs from government websites (currently SAM.gov)
- Saves RFP information in JSON format for easy viewing
- Displays a summary of collected RFPs
- Configurable via `config.json`

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
1. Gather RFPs from configured government websites
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
      "title": "IT Modernization Services",
      "agency": "Department of Defense",
      "posted_date": "2024-02-01",
      "due_date": "2024-03-15",
      "notice_id": "DOD-001-2024",
      "description": "Seeking IT modernization services for legacy systems",
      "source": "SAM.gov",
      "url": "https://sam.gov/opp/example-1"
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

This tool currently includes sample RFP data for demonstration purposes. In a production environment, you would need:
- API access to SAM.gov or other government contract websites
- Web scraping implementation with proper rate limiting and compliance
- Error handling for network issues

## License

MIT