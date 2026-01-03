from __future__ import annotations

import logging


def create_app():
    """Create a FastAPI app if FastAPI is installed.

    This project is dependency-optional; in environments where FastAPI isn't installed
    (e.g., during static analysis), importing this module must not fail.
    """

    try:
        from fastapi import FastAPI
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "FastAPI is not installed. Install backend/requirements.txt to run the API."
        ) from e

    from backend.routes.social_media import router as social_media_router

    logging.basicConfig(level=logging.INFO)

    app = FastAPI(title="Not-your-mom's-OSINT Backend")
    app.include_router(social_media_router, prefix="")
    return app


app = None
try:  # pragma: no cover
    app = create_app()
except Exception:
    # Keep import safe in minimal environments.
    app = None
