"""
Statistics helper module providing mean, median, and mode calculations.

This module provides a single function `calculate_statistics` that computes
basic statistical measures from a list of numbers.

Example:
    >>> from statistics_helper import calculate_statistics
    >>> result = calculate_statistics([1, 2, 2, 3, 4])
    >>> result["mean"]
    2.4
    >>> result["median"]
    2
    >>> result["mode"]
    2
"""

from collections import Counter
from typing import Union


def calculate_statistics(numbers: list[Union[int, float]]) -> dict[str, Union[float, int, None]]:
    """
    Calculate mean, median, and mode for a list of numbers.

    Args:
        numbers: A list of integers or floats.

    Returns:
        A dictionary with keys 'mean', 'median', and 'mode'.

    Raises:
        ValueError: If the input list is empty.

    Examples:
        >>> calculate_statistics([1, 2, 3, 4, 5])
        {'mean': 3.0, 'median': 3, 'mode': 1}

        >>> calculate_statistics([1, 2, 2, 3])
        {'mean': 2.0, 'median': 2.0, 'mode': 2}

        >>> calculate_statistics([1])
        {'mean': 1.0, 'median': 1, 'mode': 1}
    """
    # Handle empty list
    if not numbers:
        raise ValueError("Cannot calculate statistics for an empty list")

    # Calculate mean
    mean = sum(numbers) / len(numbers)

    # Calculate median
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    mid = n // 2
    if n % 2 == 0:
        median = (sorted_numbers[mid - 1] + sorted_numbers[mid]) / 2
    else:
        median = sorted_numbers[mid]

    # Calculate mode (most frequent value, smallest if tie)
    counts = Counter(numbers)
    max_count = max(counts.values())
    modes = [num for num, count in counts.items() if count == max_count]
    mode = min(modes)

    return {
        "mean": mean,
        "median": median,
        "mode": mode,
    }
