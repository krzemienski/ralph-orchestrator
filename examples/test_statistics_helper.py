"""Unit tests for statistics_helper module."""

import pytest
from statistics_helper import calculate_statistics


class TestMean:
    """Tests for mean calculation."""

    def test_mean_of_simple_list(self):
        """Mean of [1, 2, 3, 4, 5] should be 3.0."""
        result = calculate_statistics([1, 2, 3, 4, 5])
        assert result["mean"] == 3.0

    def test_mean_of_floats(self):
        """Mean of [1.5, 2.5, 3.5] should be 2.5."""
        result = calculate_statistics([1.5, 2.5, 3.5])
        assert result["mean"] == 2.5


class TestMedian:
    """Tests for median calculation."""

    def test_median_of_odd_length_list(self):
        """Median of [1, 2, 3, 4, 5] should be 3."""
        result = calculate_statistics([1, 2, 3, 4, 5])
        assert result["median"] == 3

    def test_median_of_even_length_list(self):
        """Median of [1, 2, 3, 4] should be 2.5 (average of 2 and 3)."""
        result = calculate_statistics([1, 2, 3, 4])
        assert result["median"] == 2.5

    def test_median_with_unsorted_list(self):
        """Median should work with unsorted input [5, 1, 3, 2, 4]."""
        result = calculate_statistics([5, 1, 3, 2, 4])
        assert result["median"] == 3


class TestMode:
    """Tests for mode calculation."""

    def test_mode_with_clear_mode(self):
        """Mode of [1, 2, 2, 3, 3, 3] should be 3."""
        result = calculate_statistics([1, 2, 2, 3, 3, 3])
        assert result["mode"] == 3

    def test_mode_with_tie_returns_first(self):
        """When multiple modes exist, return the smallest."""
        result = calculate_statistics([1, 1, 2, 2, 3])
        # Both 1 and 2 appear twice, return smallest
        assert result["mode"] == 1

    def test_mode_all_unique(self):
        """When all values are unique, mode is the smallest."""
        result = calculate_statistics([5, 3, 1, 4, 2])
        assert result["mode"] == 1


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_list_raises_value_error(self):
        """Empty list should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            calculate_statistics([])

    def test_single_element(self):
        """Single element [42] should return 42 for all statistics."""
        result = calculate_statistics([42])
        assert result["mean"] == 42.0
        assert result["median"] == 42
        assert result["mode"] == 42

    def test_two_elements(self):
        """Two elements [1, 3] should work correctly."""
        result = calculate_statistics([1, 3])
        assert result["mean"] == 2.0
        assert result["median"] == 2.0
        assert result["mode"] == 1  # Both have count 1, return smallest

    def test_negative_numbers(self):
        """Should handle negative numbers correctly."""
        result = calculate_statistics([-3, -1, -2, -1])
        assert result["mean"] == -1.75
        assert result["median"] == -1.5  # (-2 + -1) / 2
        assert result["mode"] == -1
