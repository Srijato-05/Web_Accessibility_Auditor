"""
AUDIT DIFF SERVICE: CONSECUTIVE SCAN COMPARATOR (DS-Y12)
=========================================================

Role: Calculates differences between consecutive runs of a domain.
Tracks new, fixed, and remaining accessibility violations.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from sqlmodel import select # type: ignore
from sqlmodel.ext.asyncio.session import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from auditor.infrastructure.persistence_models import AuditSessionModel, ViolationModel

class AuditDiffService:
    """
    Computes delta changes between consecutive accessibility audits of a domain.
    """
    
    def __init__(self, db_engine: Any):
        self.engine = db_engine

    async def calculate_diff_by_target(self, target_url: str) -> Dict[str, Any]:
        """
        Retrieves the two most recent completed master sessions for a target URL
        and computes the diff of their accessibility violations.
        """
        async with AsyncSession(self.engine) as session:
            # 1. Fetch latest two completed sessions
            query = (
                select(AuditSessionModel)
                .where(AuditSessionModel.target_url == target_url)
                .where(AuditSessionModel.status == "completed")
                .order_by(AuditSessionModel.completed_at.desc())
                .limit(2)
                .options(selectinload(AuditSessionModel.violations))
            )
            res = await session.exec(query)
            sessions = res.all()
            
            if len(sessions) < 2:
                return {
                    "status": "insufficient_data",
                    "message": "At least two completed audits are required to calculate a delta diff.",
                    "target_url": target_url,
                    "scans_found": len(sessions)
                }
                
            session_new = sessions[0]
            session_old = sessions[1]
            
            return self.diff_sessions(session_old, session_new)

    def diff_sessions(self, session_old: AuditSessionModel, session_new: AuditSessionModel) -> Dict[str, Any]:
        """
        Compares two session instances and outputs violation differences.
        """
        violations_old = session_old.violations or []
        violations_new = session_new.violations or []
        
        # Build identity maps
        # Identity key: (rule_id, url, selector)
        old_map = {
            (v.rule_id, v.url or "", v.selector or ""): v 
            for v in violations_old
        }
        new_map = {
            (v.rule_id, v.url or "", v.selector or ""): v 
            for v in violations_new
        }
        
        old_keys = set(old_map.keys())
        new_keys = set(new_map.keys())
        
        fixed_keys = old_keys - new_keys
        new_introduced_keys = new_keys - old_keys
        remaining_keys = old_keys & new_keys
        
        fixed_list = [self._serialize_violation(old_map[k]) for k in fixed_keys]
        new_list = [self._serialize_violation(new_map[k]) for k in new_introduced_keys]
        remaining_list = [self._serialize_violation(new_map[k]) for k in remaining_keys]
        
        return {
            "status": "success",
            "target_url": session_new.target_url,
            "new_session": {
                "id": str(session_new.id),
                "completed_at": session_new.completed_at.isoformat() if session_new.completed_at else None,
                "total_violations": len(violations_new)
            },
            "old_session": {
                "id": str(session_old.id),
                "completed_at": session_old.completed_at.isoformat() if session_old.completed_at else None,
                "total_violations": len(violations_old)
            },
            "summary": {
                "new_count": len(new_introduced_keys),
                "fixed_count": len(fixed_keys),
                "remaining_count": len(remaining_keys),
                "net_change": len(violations_new) - len(violations_old)
            },
            "new_violations": new_list,
            "fixed_violations": fixed_list,
            "remaining_violations": remaining_list
        }

    def _serialize_violation(self, v: ViolationModel) -> Dict[str, Any]:
        return {
            "id": str(v.id),
            "rule_id": v.rule_id,
            "url": v.url,
            "impact": v.impact,
            "description": v.description,
            "selector": v.selector,
            "help_url": v.help_url,
            "tags": v.tags or []
        }
