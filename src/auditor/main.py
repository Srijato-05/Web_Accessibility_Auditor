import sys
import asyncio
import os

# IDE PATH RECONCILIATION: Ensuring import stability for external scripts
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

# MANDATORY: Windows asyncio subprocess support for Playwright
# This MUST happen before ANY other imports (including FastAPI)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore

from auditor.presentation.api import router as api_router # type: ignore

app = FastAPI(title="Accessibility Auditor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles # type: ignore
app.include_router(api_router, prefix="/api")

# Mount reports/exports for direct linking
_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
reports_path = os.path.join(_base, "reports", "exports")
os.makedirs(reports_path, exist_ok=True)
app.mount("/reports", StaticFiles(directory=reports_path), name="reports")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return {}

@app.get("/")
def read_root():
    return {"status": "online"}
