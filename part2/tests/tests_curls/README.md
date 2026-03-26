# Introduction

The tests_curls directory is used to test API endpoints automatically.
It provides a simple way to run predefined API requests, validate responses, and generate test reports.

This tool is useful for:

- Quickly validating API endpoints
- Running repeatable API tests
- Keeping a record of test results through generated reports

## Project Structure

tests_curls/
│
├── api_tester.py
├── api_tests/
|    └── api_tests_example.json
├── run_tests.py
└── reports/

### api_tester.py

This file contains the core logic used to execute API requests.
It handles sending HTTP requests, processing responses, and validating expected results.

### tests.json

This file defines the API tests. It typically contains:

- The endpoint URL
- HTTP method (GET, POST, etc.)
- Headers
- Payload (if required)
- Expected response data

### run_tests.py

This script is the main entry point for running the test suite.
It reads the test definitions from tests.json, uses api_tester.py to execute them, and generates reports.

### reports/

This folder stores the generated test reports.
Each execution of the test suite may produce a new report summarizing:

- Passed tests
- Failed tests
- Response details

## How to Run the Tests

To execute the API tests, run the following command from the tests_curls directory:

**python api_tester.py api_tests/api_tests_example.json**

checks the api_tests file to see the relevant tests.json.

After running the tests:

The results will be displayed in the console.

A report will be generated and stored in the reports/ directory.

## Purpose

The goal of this setup is to provide a lightweight and maintainable way to test APIs using simple configuration files and Python scripts.