# Tests

This directory implements the README testing plan for the GitHub Repository Domain Classifier.

## Coverage map

| Area | Test file | Cases |
|---|---|---:|
| Backend API | `backend/test_api_classify.py` | 8 |
| GitHub data fetching | `backend/test_github_fetcher.py` | 6 |
| Feature extraction | `backend/test_feature_extractor.py` | 8 |
| Model prediction | `backend/test_model_predictor.py` | 6 |
| LLM refinement | `backend/test_llm_refiner.py` | 5 |
| Chrome extension | `extension/test_extension_static.py` | 8 |
| Integration | `integration/test_end_to_end_classification.py` | 5 |

Total: 46 pytest cases.

## Run

From the repository root:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-xdist
pytest tests/ -v
```

Coverage report:

```bash
pytest tests/ --cov=backend --cov-report=html --cov-report=term-missing
```

Markers:

```bash
pytest -m unit
pytest -m integration
pytest -m extension
```

## Notes

The backend API tests stub out GitHub API calls, SVM model loading, and Kimi/OpenAI calls. This keeps the test suite deterministic and suitable for CI.
The `.js` files in `tests/extension/` are reference Jest tests; the runnable extension checks are currently implemented in `test_extension_static.py` because `package.json` does not configure a JavaScript test runner yet.
