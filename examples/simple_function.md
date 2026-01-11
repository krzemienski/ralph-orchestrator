<!-- RUNTIME CONTEXT -->
Working Directory: /Users/nick/Desktop/ralph-orchestrator
Task File: examples/simple_function.md
<!-- END RUNTIME CONTEXT -->

<!-- RUNTIME CONTEXT -->
Working Directory: /Users/nick/Desktop/ralph-orchestrator
Task File: examples/simple_function.md
<!-- END RUNTIME CONTEXT -->

<!-- RUNTIME CONTEXT -->
Working Directory: /Users/nick/Desktop/ralph-orchestrator
Task File: examples/simple_function.md
<!-- END RUNTIME CONTEXT -->

<!-- RUNTIME CONTEXT -->
Working Directory: /Users/nick/Desktop/ralph-orchestrator
Task File: examples/simple_function.md
<!-- END RUNTIME CONTEXT -->

<!-- RUNTIME CONTEXT -->
Working Directory: /Users/nick/Desktop/ralph-orchestrator
Task File: examples/simple_function.md
<!-- END RUNTIME CONTEXT -->

<!-- RUNTIME CONTEXT -->
Working Directory: /Users/nick/Desktop/ralph-orchestrator
Task File: examples/simple_function.md
<!-- END RUNTIME CONTEXT -->

# Simple Function Example

Write a Python function that:
1. Takes a list of numbers as input
2. Returns the mean, median, and mode
3. Handles edge cases (empty list, single element)
4. Includes docstring with examples

Save the function in statistics_helper.py

Add unit tests in test_statistics_helper.py

The orchestrator will continue iterations until the function is implemented and tested

---

## Status: COMPLETE

### Implementation Summary
- **statistics_helper.py**: Contains `calculate_statistics(numbers)` function
  - Returns dict with `mean`, `median`, and `mode` keys
  - Handles edge cases: empty list (raises ValueError), single element, ties in mode
  - Full docstrings with examples

- **test_statistics_helper.py**: Contains 12 unit tests
  - TestMean: 2 tests (simple list, floats)
  - TestMedian: 3 tests (odd length, even length, unsorted)
  - TestMode: 3 tests (clear mode, ties, all unique)
  - TestEdgeCases: 4 tests (empty, single, two elements, negatives)

### All Tests Pass
```
test_statistics_helper.py::TestMean::test_mean_of_simple_list PASSED
test_statistics_helper.py::TestMean::test_mean_of_floats PASSED
test_statistics_helper.py::TestMedian::test_median_of_odd_length_list PASSED
test_statistics_helper.py::TestMedian::test_median_of_even_length_list PASSED
test_statistics_helper.py::TestMedian::test_median_with_unsorted_list PASSED
test_statistics_helper.py::TestMode::test_mode_with_clear_mode PASSED
test_statistics_helper.py::TestMode::test_mode_with_tie_returns_first PASSED
test_statistics_helper.py::TestMode::test_mode_all_unique PASSED
test_statistics_helper.py::TestEdgeCases::test_empty_list_raises_value_error PASSED
test_statistics_helper.py::TestEdgeCases::test_single_element PASSED
test_statistics_helper.py::TestEdgeCases::test_two_elements PASSED
test_statistics_helper.py::TestEdgeCases::test_negative_numbers PASSED
============================== 12 passed ==============================
```

## Completion Status
- [x] TASK_COMPLETE

When all requirements are satisfied, mark the checkbox above as complete:
`- [x] TASK_COMPLETE`

Or output `LOOP_COMPLETE` to signal the orchestrator to stop.
