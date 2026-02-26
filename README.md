# RFP-Gathering

A tool to aggregate Request for Proposals (RFPs) from government websites and save the information to a viewable file.

## Features

- Aggregates RFPs from the Indiana Department of Administration (IDOA) procurement website
- Uses web scraping with BeautifulSoup to extract RFP data
- **AI-powered education filter**: a local AI model reviews each listing and keeps only education-related RFPs before emailing them to you — no API key required
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
2. Use an AI agent to filter the listings, keeping only education-related RFPs
3. Display a summary in the terminal
4. Save all education-related RFP data to `rfp_data.json`
5. Email the education-related results to the configured recipient

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
- AI filter model (under the `ai_filter` key)
- Email recipient, SMTP host, SMTP port, and subject line

### Email Setup

The tool emails the RFP results after each run. SMTP credentials are supplied via environment variables so they are never stored in source code.

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and set your credentials:
   ```
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_smtp_password
   ```
   > **Tip:** If you use Gmail, generate an [App Password](https://support.google.com/accounts/answer/185833) and use that as `SMTP_PASSWORD`.

3. Load the variables before running the tool:
   ```bash
   set -a; source .env; set +a
   python rfp_gatherer.py
   ```

The SMTP host, port, and recipient address are configured in `config.json` under the `email` key.

### AI Education Filter

The tool uses a **local** Hugging Face zero-shot classification model to review each RFP listing and keep only those relevant to education-related topics.  No API key or internet connection is needed at run time — the model (`facebook/bart-large-mnli` by default) is downloaded automatically from Hugging Face on the first run and cached locally.

To use a different model, change the `model` field under `ai_filter` in `config.json`:

```json
"ai_filter": {
  "model": "facebook/bart-large-mnli"
}
```

> **Note:** `facebook/bart-large-mnli` is ~1.6 GB. For a smaller download (~270 MB) with slightly lower accuracy you can use `"typeform/distilbert-base-uncased-mnli"`.

If the model fails to load, all gathered RFPs are included in the email so the pipeline never silently drops data.

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