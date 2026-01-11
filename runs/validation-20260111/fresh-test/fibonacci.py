#!/usr/bin/env python3
"""Print the first 5 Fibonacci numbers."""


def fibonacci(n: int) -> list[int]:
    """Generate the first n Fibonacci numbers."""
    if n <= 0:
        return []
    if n == 1:
        return [1]

    fib = [1, 1]
    for _ in range(n - 2):
        fib.append(fib[-1] + fib[-2])
    return fib


def main() -> None:
    """Print the first 5 Fibonacci numbers."""
    numbers = fibonacci(5)
    print(", ".join(map(str, numbers)))


if __name__ == "__main__":
    main()
