from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="Untitled scan")
    language: Mapped[str] = mapped_column(String(50), default="python")
    code: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float, default=100.0)
    issue_count: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    high_count: Mapped[int] = mapped_column(Integer, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, default=0)
    low_count: Mapped[int] = mapped_column(Integer, default=0)
    llm_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="scans")
    issues = relationship("Issue", back_populates="scan", cascade="all, delete-orphan")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    rule_id: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str] = mapped_column(Text)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)

    scan = relationship("Scan", back_populates="issues")
