import sqlite3
import os

db_path = r"f:\Projects\Web Accesibility Auditor\reports\data\audit_results.db"
if not os.path.exists(db_path):
    print(f"DB not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- RECENT AUDIT SESSIONS ---")
cursor.execute("SELECT id, target_url, status, started_at, completed_at FROM audit_sessions ORDER BY created_at DESC LIMIT 5")
for row in cursor.fetchall():
    print(row)

print("\n--- RECENT VIOLATIONS ---")
cursor.execute("SELECT id, rule_id, impact FROM violations LIMIT 10")
for row in cursor.fetchall():
    print(row)

conn.close()
