import asyncio
import sys
import os

# Set Windows loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from auditor.presentation.api import get_dashboard_summary, init_db

async def main():
    await init_db()
    res = await get_dashboard_summary()
    print("KEYS:", res.keys())
    print("CATEGORIES:", res["categories"])
    print("ISSUES:", res["issues"])
    print("TOTAL SCANS:", len(res["recent_scans"]))
    nptel_scans = [s for s in res["recent_scans"] if "nptel" in s["url"].lower()]
    print("NPTEL SCANS COUNT:", len(nptel_scans))
    if nptel_scans:
        print("SAMPLE NPTEL SCAN:", nptel_scans[0])

if __name__ == "__main__":
    asyncio.run(main())
