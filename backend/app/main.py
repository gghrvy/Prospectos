import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.businesses import router as businesses_router
from app.api.senders import router as senders_router
from app.database.config import get_settings
from app.services.crawler.screenshot import SCREENSHOT_DIR

settings = get_settings()

app = FastAPI(
    title="ProspectOS API",
    description="Internal sales prospecting and website opportunity intelligence API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(businesses_router)
app.include_router(senders_router)

# Serves captured audit screenshots (desktop/mobile PNGs) so the frontend
# can display them directly, e.g. GET /screenshots/{business_id}_desktop.png.
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=SCREENSHOT_DIR), name="screenshots")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
