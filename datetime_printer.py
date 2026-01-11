#!/usr/bin/env python3
"""Print current date and time in ISO 8601 format."""

from datetime import datetime


def main():
    """Print the current datetime in ISO 8601 format."""
    current_time = datetime.now().isoformat()
    print(current_time)


if __name__ == "__main__":
    main()
