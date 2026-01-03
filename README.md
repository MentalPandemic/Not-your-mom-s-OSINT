# Not-your-mom's-OSINT

This repository contains the early backend building blocks for an OSINT aggregation platform.

## Backend

The initial implementation focuses on a comprehensive social media enrichment module.

- Code: `backend/`
- Docs: `backend/docs/SOCIAL_MEDIA_INTEGRATION.md`

To run the API (after installing dependencies):

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app:app --reload
```
