import sys
import asyncio
import os

# --- CRITICAL WINDOWS FIX: MUST RUN BEFORE ANY OTHER IMPORTS ---
if sys.platform == 'win32':
    # High-Priority: Force ProactorEventLoop to support subprocesses (Playwright)
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print(">>> System: Windows Local Loop Policy set to 'Proactor' (PE-Z10 Compliance)")

import uvicorn

if __name__ == "__main__":
    # Ensure src is in python path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
    
    # Run the FastAPI app
    # We don't use reload=True here to avoid loop policy issues in sub-processes, 
    # but we'll leave it for dev-mode if needed.
    uvicorn.run(
        "auditor.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        app_dir="src"
    )
