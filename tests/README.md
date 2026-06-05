# Tests

This directory contains backend, extension, integration tests and fixtures.

## Structure

- `backend/`: tests for Flask API, feature extraction, model prediction, and LLM refinement.
- `extension/`: tests for Chrome Extension parsing and badge rendering.
- `integration/`: end-to-end classification tests.
- `fixtures/`: sample README files and mock API responses.

## Run Python tests

```bash
pytest tests/ -v
