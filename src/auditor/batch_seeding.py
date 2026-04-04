import asyncio
import json
import csv
import os
import sys
import argparse

# IDE PATH RECONCILIATION: Redundant path hinting for static analysis
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import List, Dict, Any, Optional, Tuple, cast
from sqlmodel import SQLModel, select # type: ignore
from sqlalchemy.ext.asyncio import create_async_engine # type: ignore
from sqlmodel.ext.asyncio.session import AsyncSession

from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel, TargetModel # type: ignore
from auditor.infrastructure.target_repository import SqlAlchemyTargetRepository # type: ignore
from auditor.domain.models import AuditTarget, DomainStatus # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore

DATABASE_URL = "sqlite+aiosqlite:///./reports/data/audit_results.db"

# Expanded Category Matrix
DEFAULT_SECTOR_MATRIX = {
    "Government": [
        "https://india.gov.in",
        "https://www.digitalindia.gov.in",
        "https://mygov.in",
        "https://uidai.gov.in",
        "https://nptel.ac.in"
    ],
    "Banking & Finance": [
        "https://www.onlinesbi.sbi",
        "https://www.hdfcbank.com",
        "https://www.icicibank.com",
        "https://www.axisbank.com",
        "https://www.kotak.com"
    ],
    "Technology & Services": [
        "https://www.isro.gov.in",
        "https://www.tcs.com",
        "https://www.infosys.com",
        "https://www.wipro.com"
    ],
    "Telecom": [
        "https://www.jio.com",
        "https://www.airtel.in",
        "https://www.vi.in",
        "https://www.bsnl.co.in"
    ],
    "E-commerce & Retail": [
        "https://www.flipkart.com",
        "https://www.amazon.in",
        "https://www.nykaa.com",
        "https://www.bigbasket.com",
        "https://www.zomato.com"
    ],
    "Healthcare": [
        "https://www.nhp.gov.in",
        "https://www.apollohospitals.com",
        "https://www.fortishealthcare.com",
        "https://www.maxhealthcare.in"
    ],
    "Education": [
        "https://www.ugc.ac.in",
        "https://www.ignou.ac.in",
        "https://www.iitb.ac.in",
        "https://www.iitd.ac.in"
    ]
}

async def seed_from_matrix(batch_repo: SqlAlchemyTargetRepository, matrix: Dict[str, List[str]]) -> Tuple[int, int]:
    """Seeds the database from a provided matrix dictionary."""
    total_added: int = 0
    total_skipped: int = 0
    
    for category, urls in matrix.items():
        print(f"\n[Auditor] Category: {category}")
        for url in urls:
            # Duplicate check
            existing = await batch_repo.get_domain_by_url(url)
            if existing:
                print(f" -> Skipping (Exists): {url}")
                total_skipped += 1 # type: ignore
                continue
                
            print(f" -> Registering: {url}")
            new_target = AuditTarget(url=url)
            await batch_repo.add_domain(new_target)
            total_added += 1 # type: ignore
            
    return total_added, total_skipped

async def seed_from_file(batch_repo: SqlAlchemyTargetRepository, filepath: str) -> Tuple[int, int]:
    """Seeds the database from a JSON or CSV file."""
    if not os.path.exists(filepath):
        print(f"[Error] File not found: {filepath}")
        return 0, 0
        
    urls = []
    if filepath.endswith('.json'):
        with open(filepath, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                urls = data
            elif isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        urls.extend(v)
    elif filepath.endswith('.csv'):
        with open(filepath, 'r') as f:
            # Handle potential headers
            reader = csv.reader(f)
            for row in reader:
                if row:
                    url = row[0].strip()
                    if url.startswith('http'):
                        urls.append(url)
    
    if not urls:
        print(f"[Warning] No valid URLs found in {filepath}")
        return 0, 0
        
    matrix = {"Imported": urls}
    return await seed_from_matrix(batch_repo, matrix)

async def main():
    parser = argparse.ArgumentParser(description="Advanced Audit Target Seeding Utility")
    parser.add_argument("--file", help="Path to JSON or CSV file for bulk import")
    parser.add_argument("--category", help="Specify a single category to seed from the matrix", default=None)
    args = parser.parse_args()

    print("[Auditor] Initializing Advanced Seeding Engine...")
    
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # SQLModel alternative to Base.metadata.create_all
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as db_session:
        batch_repo = SqlAlchemyTargetRepository(db_session)
        
        added, skipped = 0, 0
        
        if args.file:
            added, skipped = await seed_from_file(batch_repo, args.file)
        elif args.category:
            if args.category in DEFAULT_SECTOR_MATRIX:
                matrix = {args.category: DEFAULT_SECTOR_MATRIX[args.category]}
                added, skipped = await seed_from_matrix(batch_repo, matrix)
            else:
                print(f"[Error] Category not found: {args.category}")
                return
        else:
            added, skipped = await seed_from_matrix(batch_repo, DEFAULT_SECTOR_MATRIX)

    print(f"\n[Auditor] SEEDING COMPLETE.")
    print(f" -> Targets Added: {added}") # type: ignore
    print(f" -> Targets Skipped: {skipped}") # type: ignore

if __name__ == "__main__":
    asyncio.run(main())
