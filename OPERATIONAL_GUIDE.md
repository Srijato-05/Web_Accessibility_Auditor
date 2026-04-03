# Auditor Platform - Operational Guide [v0.1.0]

--- [ SYSTEM NOTIFICATION ] ---
This console provides direct access to high-performance, automated auditing infrastructure.

--- [ ENVIRONMENT SETUP ] ---
1. Prepare Environment:
   $ poetry install

2. Initialize Browser Components:
   $ poetry run playwright install chromium

--- [ EXECUTION MODES ] ---

>> 1. BATCH AUDIT MANAGEMENT (Multi-Domain Automated Process)
   The primary command for large-scale batch audits.
   
   - To Add a New Audit Target:
     $ poetry run python -m auditor.batch_audit --add <URL>

   - To Execute a High-Concurrency Batch Audit:
     $ poetry run python -m auditor.batch_audit

>> 2. SITE AUDIT (Recursive Crawl & Audit)
   Used for deep discovery of a specific domain's page ecosystem.
   $ poetry run python -m auditor.site_audit <URL>

>> 3. SINGLE URL AUDIT (Precision Scan)
   Used for auditing of a specific landing page or asset.
   $ poetry run python -m auditor.single_url <URL>

--- [ DIAGNOSTICS & METRICS ] ---

>> SYSTEM LOGS
   The Auditor core maintains an audit trail in `auditor.log`.

>> ANALYTICS CONSOLE
   Inspect the current results database:
   $ poetry run python check_db.py
