# Method

This document describes the repository classification method.

The system combines:

1. README keyword extraction
2. SVM-based repository classification
3. Low-confidence detection
4. LLM-assisted refinement using GPT or Kimi

The Chrome Extension sends repository information to the Flask backend.

The backend extracts README features, performs SVM prediction, and optionally uses an LLM for secondary judgment when the model confidence is low.
