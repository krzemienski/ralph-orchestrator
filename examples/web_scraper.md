# Web Scraper Example

Build a Python web scraper that:

1. Scrapes the top stories from Hacker News (https://news.ycombinator.com)
2. Extracts:
   - Title
   - URL
   - Points
   - Number of comments
   - Submission time

3. Saves data to both:
   - JSON file (hn_stories.json)
   - CSV file (hn_stories.csv)

4. Implements rate limiting (1 request per second)
5. Includes error handling for network issues
6. Adds logging for debugging

Requirements:
- Use requests and BeautifulSoup
- Follow robots.txt guidelines
- Include a main() function
- Add command-line argument for number of stories to fetch

Save as hn_scraper.py

The orchestrator will continue iterations until the scraper is fully implemented

---

## Status: COMPLETE

### Implementation Summary (2026-01-10)

The `hn_scraper.py` script has been fully implemented with all required features:

#### Features Implemented:
- [x] Scrapes top stories from Hacker News
- [x] Extracts: Title, URL, Points, Comments, Submission time
- [x] Saves to JSON file (hn_stories.json)
- [x] Saves to CSV file (hn_stories.csv)
- [x] Rate limiting (1 request per second)
- [x] Error handling for network issues (timeout, connection, HTTP errors)
- [x] Logging for debugging (INFO and DEBUG levels)
- [x] Uses requests and BeautifulSoup
- [x] Includes main() function
- [x] Command-line arguments: --count/-n, --verbose/-v, --output-dir/-o

#### Usage:
```bash
# Scrape 30 stories (default)
python hn_scraper.py

# Scrape 10 stories
python hn_scraper.py --count 10

# Scrape with verbose logging
python hn_scraper.py -n 5 --verbose

# Specify output directory
python hn_scraper.py -n 20 -o ./output
```

#### Output Files:
- `hn_stories.json`: JSON array of story objects
- `hn_stories.csv`: CSV with headers (rank, title, url, points, comments, submission_time)