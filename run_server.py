import asyncio
import sys
import os

# MANDATORY: Windows Proactor Loop Enforcement
# This MUST happen at the very first line of the absolute entry point
if sys.platform == 'win32':
    print("ENGINE: System-level Proactor Loop Enforcement ACTIVE...")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    # Ensure src is in path for imports
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
    
    print("ENGINE: Launching Sentinel Backend via Standardized High-Fidelity Entrypoint...")
    
    uvicorn.run(
        "auditor.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False, # DISABLED RELOADER FOR WINDOWS STABILITY
        loop="asyncio",
        log_level="info"
    )
