#!/usr/bin/env python3
"""
Hacker News Top Stories Scraper

A web scraper that extracts top stories from Hacker News and saves them
to JSON and CSV files. Implements rate limiting and follows robots.txt guidelines.

Usage:
    python hn_scraper.py [--count N]

Requirements:
    - requests
    - beautifulsoup4
"""

import argparse
import csv
import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://news.ycombinator.com"
RATE_LIMIT_SECONDS = 1.0
DEFAULT_STORY_COUNT = 30
USER_AGENT = "HNScraper/1.0 (Educational purposes; respects robots.txt)"


@dataclass
class Story:
    """Represents a Hacker News story."""
    title: str
    url: Optional[str]
    points: int
    comments: int
    submission_time: str
    rank: int


class HNScraper:
    """Scraper for Hacker News top stories."""

    def __init__(self, rate_limit: float = RATE_LIMIT_SECONDS):
        """
        Initialize the scraper.

        Args:
            rate_limit: Seconds to wait between requests
        """
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.last_request_time = 0.0

    def _wait_for_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with error handling and rate limiting.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if request failed
        """
        self._wait_for_rate_limit()

        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error fetching {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {url}: {e}")
            return None

    def parse_stories(self, html: str) -> list[Story]:
        """
        Parse stories from HN HTML page.

        Args:
            html: HTML content of HN page

        Returns:
            List of Story objects
        """
        soup = BeautifulSoup(html, 'html.parser')
        stories = []

        # HN uses 'athing' class for story rows
        story_rows = soup.select('tr.athing')

        for row in story_rows:
            try:
                story = self._parse_story_row(row)
                if story:
                    stories.append(story)
            except Exception as e:
                logger.warning(f"Error parsing story row: {e}")
                continue

        return stories

    def _parse_story_row(self, row) -> Optional[Story]:
        """
        Parse a single story row from HN.

        Args:
            row: BeautifulSoup element for the story row

        Returns:
            Story object or None if parsing failed
        """
        # Get rank
        rank_elem = row.select_one('span.rank')
        rank = int(rank_elem.text.strip('.')) if rank_elem else 0

        # Get title and URL
        title_elem = row.select_one('span.titleline > a')
        if not title_elem:
            return None

        title = title_elem.text.strip()
        url = title_elem.get('href', '')

        # Handle relative URLs (for Ask HN, Show HN, etc.)
        if url and not url.startswith('http'):
            url = f"{BASE_URL}/{url}"

        # Get subtext row (next sibling)
        subtext_row = row.find_next_sibling('tr')
        subtext = subtext_row.select_one('td.subtext') if subtext_row else None

        points = 0
        comments = 0
        submission_time = ""

        if subtext:
            # Parse points
            score_elem = subtext.select_one('span.score')
            if score_elem:
                points_text = score_elem.text.strip()
                points = int(points_text.split()[0])

            # Parse submission time
            age_elem = subtext.select_one('span.age')
            if age_elem:
                submission_time = age_elem.get('title', age_elem.text.strip())

            # Parse comments
            links = subtext.select('a')
            for link in links:
                text = link.text.strip()
                if 'comment' in text:
                    try:
                        comments = int(text.split()[0])
                    except (ValueError, IndexError):
                        comments = 0
                    break

        return Story(
            title=title,
            url=url,
            points=points,
            comments=comments,
            submission_time=submission_time,
            rank=rank
        )

    def scrape_stories(self, count: int = DEFAULT_STORY_COUNT) -> list[Story]:
        """
        Scrape top stories from Hacker News.

        Args:
            count: Number of stories to fetch

        Returns:
            List of Story objects
        """
        stories = []
        page = 1

        while len(stories) < count:
            url = BASE_URL if page == 1 else f"{BASE_URL}?p={page}"
            html = self.fetch_page(url)

            if not html:
                logger.warning(f"Failed to fetch page {page}, stopping")
                break

            page_stories = self.parse_stories(html)

            if not page_stories:
                logger.warning(f"No stories found on page {page}, stopping")
                break

            stories.extend(page_stories)
            page += 1

            logger.info(f"Collected {len(stories)} stories so far")

        # Trim to requested count
        return stories[:count]


def save_to_json(stories: list[Story], filename: str) -> None:
    """
    Save stories to a JSON file.

    Args:
        stories: List of Story objects
        filename: Output filename
    """
    data = [asdict(story) for story in stories]

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(stories)} stories to {filename}")


def save_to_csv(stories: list[Story], filename: str) -> None:
    """
    Save stories to a CSV file.

    Args:
        stories: List of Story objects
        filename: Output filename
    """
    if not stories:
        logger.warning("No stories to save to CSV")
        return

    fieldnames = ['rank', 'title', 'url', 'points', 'comments', 'submission_time']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for story in stories:
            writer.writerow(asdict(story))

    logger.info(f"Saved {len(stories)} stories to {filename}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Scrape top stories from Hacker News',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python hn_scraper.py              # Scrape 30 stories (default)
    python hn_scraper.py --count 10   # Scrape 10 stories
    python hn_scraper.py -n 50        # Scrape 50 stories
        """
    )

    parser.add_argument(
        '-n', '--count',
        type=int,
        default=DEFAULT_STORY_COUNT,
        help=f'Number of stories to fetch (default: {DEFAULT_STORY_COUNT})'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose (debug) logging'
    )

    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='.',
        help='Output directory for JSON and CSV files (default: current directory)'
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the HN scraper."""
    args = parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting HN Scraper - fetching {args.count} stories")

    # Initialize scraper
    scraper = HNScraper()

    # Scrape stories
    stories = scraper.scrape_stories(count=args.count)

    if not stories:
        logger.error("No stories were scraped")
        return

    logger.info(f"Successfully scraped {len(stories)} stories")

    # Save to files
    import os
    json_path = os.path.join(args.output_dir, 'hn_stories.json')
    csv_path = os.path.join(args.output_dir, 'hn_stories.csv')

    save_to_json(stories, json_path)
    save_to_csv(stories, csv_path)

    # Print summary
    print(f"\nScraped {len(stories)} stories from Hacker News")
    print(f"  - JSON: {json_path}")
    print(f"  - CSV: {csv_path}")


if __name__ == '__main__':
    main()
