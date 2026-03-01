"""
IntelResponse – FastAPI application entry point.
"""

from fastapi import FastAPI

app = FastAPI(
    title="IntelResponse",
    description="AI-powered incident intelligence platform",
    version="0.1.0",
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "IntelResponse API is running"}


# TODO: Add incident CRUD routes
# TODO: Add IOC extraction routes
# TODO: Add risk scoring routes
# TODO: Add similarity search routes
# TODO: Add CORS middleware for frontend
