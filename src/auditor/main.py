from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Add src to python path if not exist
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auditor.presentation.api import router as api_router

app = FastAPI(title="Accessibility Auditor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "online"}
