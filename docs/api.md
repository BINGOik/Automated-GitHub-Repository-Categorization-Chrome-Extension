# API Documentation

This document describes the backend API used by the Chrome Extension.

## POST /domain

Classifies a GitHub repository into a development domain.

### Request

```json
{
  "owner": "facebook",
  "repo": "react"
}
Response
{
  "category": "Web Frontend",
  "confidence": 0.92
}
Notes
The API is provided by the Flask backend service.
