"""Accessibility Auditor: Core Package Structure."""
import sys
import asyncio

# FIX: Windows asyncio subprocess support for Playwright
if sys.platform == 'win32':
    try:
        # Check if a loop is already running; if so, we might not be able to change policy easily
        # but setting it here covers the case where uvicorn hasn't started the event loop yet.
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass
