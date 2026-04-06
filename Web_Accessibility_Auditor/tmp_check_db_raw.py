import sqlite3
import os
import json

db_path = r"f:\Projects\Web Accesibility Auditor\reports\data\audit_results.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, target_url, focus_path, aria_events FROM audit_sessions ORDER BY created_at DESC LIMIT 1")
row = cursor.fetchone()

if row:
    session_id, url, focus_path, aria_events = row
    print(f"Session ID: {session_id}")
    print(f"Target: {url}")
    
    # Check focus_path
    try:
        fp = json.loads(focus_path) if focus_path else []
    except:
        fp = []
    print(f"Focus Path Points: {len(fp)}")
    if fp:
        print(f"Sample Point: {fp[0]}")
        
    # Check aria_events
    try:
        ae = json.loads(aria_events) if aria_events else []
    except:
        ae = []
    print(f"ARIA Events: {len(ae)}")
    if ae:
        print(f"Sample Event: {ae[0]}")
else:
    print("No sessions found.")

conn.close()
