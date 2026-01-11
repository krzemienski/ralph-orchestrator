#!/usr/bin/env python3
"""
Date Script - Prints the current date in ISO format.

This script outputs the current date in YYYY-MM-DD format.
"""

from datetime import date


def main():
    """Print the current date in ISO format (YYYY-MM-DD)."""
    today = date.today()
    print(today.isoformat())


if __name__ == "__main__":
    main()
