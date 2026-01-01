#!/usr/bin/env python3

"""
Main entry point for Not-your-mom's-OSINT platform
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.main import app
import uvicorn

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        workers=4
    )