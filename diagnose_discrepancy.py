import asyncio
import os
import sys
import json
from uuid import UUID

# Resolve sys.path to import from src
root_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(root_path, "src"))

from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel
from auditor.presentation.api import get_audit_violations

async def main():
    database_url = "sqlite+aiosqlite:///./reports/data/audit_results.db"
    engine = create_async_engine(database_url, echo=False)
    
    async with AsyncSession(engine) as db_session:
        # Get latest completed session
        stmt = select(AuditSessionModel).where(AuditSessionModel.status == "completed").order_by(AuditSessionModel.started_at.desc()).limit(1)
        res = await db_session.exec(stmt)
        session = res.first()
        
        if not session:
            print("No completed sessions found in database.")
            return
            
        print("=============================================================")
        print("                  DIAGNOSTIC DISCREPANCY ANALYSIS            ")
        print("=============================================================")
        print(f"Session ID:  {session.id}")
        print(f"Target URL:  {session.target_url}")
        print(f"Started At:  {session.started_at}")
        
        # Fetch all raw database violations for this session
        v_stmt = select(ViolationModel).where(ViolationModel.session_id == session.id)
        v_res = await db_session.exec(v_stmt)
        raw_violations = v_res.all()
        
        # 1. Total rows
        db_rows_count = len(raw_violations)
        print(f"\n1. DB Row Count (violations table): {db_rows_count}")
        
        # 2. Total nodes/elements in raw database
        total_raw_nodes = 0
        for v in raw_violations:
            nodes_list = v.nodes or []
            total_raw_nodes += len(nodes_list) if nodes_list else 1
        print(f"2. Total Failed Elements (nodes) in DB: {total_raw_nodes}")
        
        # 3. Grouped violations returned by API
        grouped_violations = await get_audit_violations(str(session.id))
        print(f"3. Grouped Violations (returned to UI): {len(grouped_violations)}")
        
        sum_grouped_occurrences = sum(v.get("occurrences", 1) for v in grouped_violations)
        print(f"4. Sum of occurrences in Grouped Violations: {sum_grouped_occurrences}")
        
        # 4. Severity Tally in Raw DB vs Grouped UI
        db_critical = sum(1 for v in raw_violations if (v.impact or "").lower() == "critical")
        db_major = sum(1 for v in raw_violations if (v.impact or "").lower() in ("serious", "major"))
        db_minor = db_rows_count - db_critical - db_major
        
        print("\n--- SEVERITY TALLY ---")
        print(f"{'Severity Category':<25} | {'DB Rows Count':<15} | {'UI Grouped Occurrences'}")
        print("-" * 65)
        
        ui_critical = 0
        ui_serious = 0
        ui_moderate = 0
        ui_minor = 0
        for v in grouped_violations:
            for node in v.get("nodes", []):
                imp = (node.get("impact") or v.get("impact") or "").lower()
                if imp == "critical":
                    ui_critical += 1
                elif imp in ("serious", "major"):
                    ui_serious += 1
                elif imp == "moderate":
                    ui_moderate += 1
                elif imp == "minor":
                    ui_minor += 1
        
        print(f"{'Critical':<25} | {db_critical:<15} | {ui_critical}")
        print(f"{'Major (Serious/Major)':<25} | {db_major:<15} | {ui_serious} (Serious) + {ui_moderate} (Moderate)")
        print(f"{'Minor (Minor/Moderate)':<25} | {db_minor:<15} | {ui_minor}")
        
        # 5. Agent Breakdown with Raw Rows vs Nodes
        print("\n--- AGENT BREAKDOWN ---")
        print(f"{'Agent':<12} | {'DB Rows':<8} | {'DB Nodes':<9} | {'UI Grouped':<10} | {'UI Occurrences'}")
        print("-" * 60)
        for agent in ["axe", "visual", "motor", "cognitive", "neural"]:
            agent_raw_violations = [v for v in raw_violations if (v.agent or "axe").lower() == agent]
            agent_rows = len(agent_raw_violations)
            
            agent_nodes = 0
            for v in agent_raw_violations:
                nodes_list = v.nodes or []
                agent_nodes += len(nodes_list) if nodes_list else 1
                
            agent_grouped = [v for v in grouped_violations if (v.get("agent") or "axe").lower() == agent]
            agent_grouped_count = len(agent_grouped)
            agent_grouped_occ = sum(v.get("occurrences", 1) for v in agent_grouped)
            
            print(f"{agent:<12} | {agent_rows:<8} | {agent_nodes:<9} | {agent_grouped_count:<10} | {agent_grouped_occ}")

if __name__ == "__main__":
    asyncio.run(main())
