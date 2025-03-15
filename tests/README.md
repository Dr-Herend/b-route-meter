# B-Route Meter Tests

This directory contains the test suite for the B-Route Meter integration.

## Directory Structure

```
tests/
├── __init__.py          # Test package initialization
├── conftest.py         # Common test fixtures and configuration
├── test_diagnostic.py  # Tests for diagnostic functionality
└── README.md          # This documentation
```

## Overview

The test suite is organized according to Python project best practices, with tests separated from the main source code. This makes the tests easier to maintain and run, while keeping the source code directory clean.

## Running Tests

Using uv (recommended):

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_diagnostic.py

# Run with coverage report
uv run pytest --cov
```

## Test Coverage

The test suite includes:

1. Diagnostic Feature Tests
   - Data structure validation
   - Update timing verification
   - Error handling
   - Data format checks

2. Integration Tests
   - Device connection
   - Data collection
   - Update scheduling

## Writing Tests

When adding new tests:

1. Follow existing test structure
2. Include docstrings explaining test purpose
3. Use fixtures from conftest.py where appropriate
4. Keep tests focused and isolated
