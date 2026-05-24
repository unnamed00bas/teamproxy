from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import NodeStatus
from app.schemas.common import TimestampedSchema


class NodeBase(BaseModel):
    site_id: str
    hostname: str
    private_ip: str | None = None
    platform: str | None = None
    is_gateway: bool = False
    notes: str | None = None


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    site_id: str | None = None
    hostname: str | None = None
    private_ip: str | None = None
    platform: str | None = None
    is_gateway: bool | None = None
    status: NodeStatus | None = None
    notes: str | None = None


class NodeRead(TimestampedSchema, NodeBase):
    status: NodeStatus
