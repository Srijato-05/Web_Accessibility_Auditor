from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
from sqlmodel import SQLModel, Field # type: ignore
from sqlalchemy import Column, JSON, MetaData # type: ignore

# Separate metadata instance for TaskModel to avoid SQLModel global registry conflicts
task_metadata = MetaData()

class TaskModel(SQLModel, table=True):
    __tablename__ = "audit_task_queue"
    __table_args__ = {"extend_existing": True}
    metadata = task_metadata
    
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str
    data: Dict[str, Any] = Field(sa_column=Column(JSON))
    metadata_json: Dict[str, Any] = Field(sa_column=Column("metadata", JSON)) # Rename to avoid conflict with MetaData property
    status: str = Field(default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    created_at: datetime = Field(default_factory=datetime.now)
