import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.businesses import router as businesses_router
from app.api.senders import router as senders_router
from app.api.gmail import router as gmail_router
from app.database.config import get_settings
from app.services import demo_data
from app.services.crawler.screenshot import SCREENSHOT_DIR
from app.services.outreach_scheduler import start_scheduler, stop_scheduler

settings = get_settings()

app = FastAPI(
    title="ProspectOS API",
    description="Internal sales prospecting and website opportunity intelligence API.",
    version="0.1.0",
)


@app.middleware("http")
async def enforce_demo_mode(request: Request, call_next):
    """Make the API—not the browser—the final public-demo safety boundary.

    Only the prepared catalogue and replaying an existing prepared audit are
    available.  In particular, OAuth, Gmail, discovery, URL crawling, CSV
    export/import, SQL mutations, and AI-backed writes are not reachable.
    """
    if not get_settings().is_demo_mode:
        return await call_next(request)

    path = request.url.path.rstrip("/") or "/"
    method = request.method.upper()
    business_detail_read = (
        path.startswith("/api/businesses/")
        and len(path.split("/")) == 4
        and demo_data.is_demo_business(path.rsplit("/", 1)[-1])
    )
    safe_get = path in {"/health", "/api/businesses", "/api/gmail/status"} or business_detail_read or path.startswith("/docs") or path.startswith("/openapi")
    safe_demo_audit = (
        method == "POST"
        and path.startswith("/api/businesses/")
        and path.endswith("/audit")
        and demo_data.is_demo_business(path.split("/")[-2])
    )
    if (method in {"GET", "HEAD", "OPTIONS"} and safe_get) or safe_demo_audit:
        return await call_next(request)
    return JSONResponse(
        status_code=403,
        content={"detail": "Demo Mode is read-only. Prepared sample data is available, but live operations are disabled."},
    )


@app.on_event("startup")
def start_background_workers() -> None:
    if not get_settings().is_demo_mode:
        start_scheduler()


@app.on_event("shutdown")
def stop_background_workers() -> None:
    if not get_settings().is_demo_mode:
        stop_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(businesses_router)
app.include_router(senders_router)
app.include_router(gmail_router)

# Serves captured audit screenshots (desktop/mobile PNGs) so the frontend
# can display them directly, e.g. GET /screenshots/{business_id}_desktop.png.
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=SCREENSHOT_DIR), name="screenshots")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
