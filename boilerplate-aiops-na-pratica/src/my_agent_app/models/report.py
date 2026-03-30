import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from my_agent_app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    markdown: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(default="EM_ANALISE")
    event_uids: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    fix_result: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_reports_event_uids", "event_uids", postgresql_using="gin"),
    )
