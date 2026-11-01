"""CampusEats API entry point."""
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.menu_items.router import router as menu_router

logger = logging.getLogger("campuseats")

app = FastAPI(
    title="CampusEats API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

# Create the tables that are missing. On Vercel there is no startup event,
# so this runs when the app is first loaded.
try:
    init_db()
except Exception:
    logger.exception("Could not create the database tables")

app.include_router(menu_router)


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# dist/ only exists after `npm run build`; in dev the Vite server serves the UI.
if FRONTEND_DIR.is_dir():
    app.frontend("/", directory=FRONTEND_DIR)