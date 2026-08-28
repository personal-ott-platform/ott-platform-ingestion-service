"""
This module contains the main application for the uploads service.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.v1.uploads import router as uploads_router
from app.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="Video Ingestion Pipeline",
    description="APIs for complete video ingestion pipelines",
    version="1.0.0",
)

app.include_router(uploads_router)

@app.get('/', include_in_schema=False)
async def root():
    """
    Redirect to the docs.
    """
    return RedirectResponse(url='/docs')
