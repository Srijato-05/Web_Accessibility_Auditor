# Technical Audit & Deep Analysis: Web Accessibility Auditor (Current Status)

This document provides a comprehensive review of the current architectural, logical, coding, and API-level flaws within the Web Accessibility Auditor suite, detailing what has been resolved and what issues are still outstanding.

---

## 1. Resolved Flaws & Hardening Milestones

### A. The Axe-Core Result Extraction Silencing (Resolved)
* **Status**: Fully Fixed.
* **Resolution**: Modified the page scan routine in `PlaywrightEngine` to verify if the return payload is an `AxeResults` object and successfully extract violations from `.response["violations"]` instead of returning 0 results.

### B. Runtime DDL / Migration Overhead (Resolved)
* **Status**: Fully Fixed.
* **Resolution**: Removed all redundant `await init_db()` calls inside FastAPI route handlers. Registered `init_db()` strictly under the `@app.on_event("startup")` app lifecycle hook inside `src/auditor/main.py` so database schemas are provisioned once at system start.

### C. Server-Side Request Forgery (SSRF) Protection (Resolved)
* **Status**: Fully Fixed.
* **Resolution**: Implemented the `is_safe_url` helper in `src/auditor/presentation/api.py`. URLs resolving to private subnets or loopback interfaces (e.g. AWS meta-data IP, `127.*`, `10.*`) are rejected with an HTTP 400 Bad Request. Supports local testing via the `AUDITOR_ALLOW_LOCAL` environment flag.

### D. Stable API Violation IDs (Resolved)
* **Status**: Fully Fixed.
* **Resolution**: Replaced transient `uuid.uuid4()` generation with stable, deterministic UUIDs generated via `uuid.uuid5` (based on the session ID, rule ID, and target element selector string).

### E. Worker Backpressure & Resource Monitoring (Resolved)
* **Status**: Fully Fixed.
* **Resolution**: Integrated a resource monitor (`psutil`) in `AuditWorker` that tracks CPU and RAM usage. The worker defers popping new tasks from the queue (sleeping for 5 seconds) if utilization exceeds the threshold (default `85.0%`).

### F. SQLite Repository Mapper Forensics (Resolved)
* **Status**: Fully Fixed.
* **Resolution**: Bound missing audit metadata columns (`agent`, `compliance_level`, `category`, `severity_matrix`, `url`) in the SQLModel repository mapper (`SqlAlchemyAuditRepository.get_session`) so that violation entities maintain their original values when re-loaded.

### G. TigerGraph Dead Code Removal (Resolved)
* **Status**: Fully Cleaned.
* **Resolution**: The dead module `tigergraph_repository.py` has been deleted from the filesystem, and residual dashboard summary status checks have been retargeted to Neo4j.

---

## 2. Outstanding Flaws & Issues (Requires Action)

### A. Temporary File Disk Leakage (C: Drive space consumption)
* **Vulnerability**: In `src/auditor/infrastructure/pdf_reporter.py` (lines 328-330), HTML reports are created using `tempfile.NamedTemporaryFile()` which writes directly to the system standard temp path (on Windows this resolves to the `C:` drive).
* **Impact**: Since your `C:` drive is almost full, generating large reports or running crawl sessions with high page counts runs a severe risk of failing midway or crashing the host OS due to lack of disk space.
* **Remediation**: Reconfigure the temp file creation to write to the `EXPORTS_DIR` or a custom directory on the `F:` drive by supplying the `dir` parameter (e.g. `dir=os.path.dirname(output_pdf_path)`).

### B. Fire-and-Forget Thread / Task Panics (Neo4j Calls)
* **Vulnerability**: The audit service dispatches batch upserts to Neo4j using `asyncio.create_task(self.tg_repo.upsert_component_violations_batch_async(tg_batch))`.
* **Impact**: If Neo4j goes offline during an audit session, these tasks fail silently in the background with unhandled exceptions. In addition, if the application shuts down, these pending tasks are killed immediately without finishing the write, resulting in graph database inconsistency.
* **Remediation**: Track and await these tasks at the end of the audit session (e.g., maintaining a list of background futures and using `asyncio.gather`), or route them through the standard task queue.

### C. Lack of Explicit Transaction Boundaries
* **Vulnerability**: Endpoints and service modules share the SQLModel/SQLAlchemy `AsyncSession` but write records without wrapping them in explicit transaction contexts (`async with db_session.begin()`).
* **Impact**: If a crawl service fails halfway (e.g. after writing 10 violations but before updating the session state to `COMPLETED`), the database is left in a corrupted or inconsistent state with no rollbacks.
* **Remediation**: Use database transactions so that writes are atomically committed only upon full audit completion.

### D. Dead Module Footprint (`RulesNexus`)
* **Vulnerability**: The rule database/nexus class `src/auditor/domain/rules_nexus.py` remains in the codebase but has 0% coverage and is never imported or utilized in the application stack.
* **Impact**: Bloats codebase footprint.
* **Remediation**: Clean up and delete `rules_nexus.py` or integrate it as the central schema validator.

### E. Low Test Coverage on High-Complexity Code (Resolved)
* **Status**: Fully Fixed.
* **Resolution**: Created `tests/test_contrast.py` containing a comprehensive test suite for `contrast.py` and `color_rules.py`, verifying parsing, WCAG thresholds, similarity checks, and visual cue indicators.

### F. SQLModel & Redis Deprecation Warnings (Resolved)
* **Status**: Fully Fixed.
* **Resolution**: Replaced `session.execute` with `session.exec` to comply with the SQLModel APIs (and corrected resulting `.scalar()` invocation failures to `.first()`), updated Redis disconnect routines to use `aclose()` instead of the deprecated `close()`, and replaced deprecated Python `datetime.utcnow()` calls with timezone-aware variants.

### G. FastAPI and Test Suite Telemetry/Mock Warnings (Resolved)
* **Status**: Fully Fixed.
* **Resolution**: Migrated deprecated FastAPI `startup` events to async `lifespan` context handlers, renamed helper classes to prevent false pytest collection warnings, and resolved mock coroutine leak warnings in mock page and wait_for timeouts.

