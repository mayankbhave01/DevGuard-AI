from datetime import datetime
from pydantic import BaseModel, Field


class ScanCreate(BaseModel):
    title: str = Field(default="Untitled scan", max_length=200)
    language: str = Field(default="python", max_length=50)
    code: str = Field(min_length=1, max_length=200_000)
    use_llm: bool = False


class IssueOut(BaseModel):
    id: int
    rule_id: str
    category: str
    severity: str
    title: str
    description: str
    suggestion: str
    line: int | None
    snippet: str | None

    model_config = {"from_attributes": True}


class ScanSummary(BaseModel):
    id: int
    title: str
    language: str
    score: float
    issue_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanDetail(ScanSummary):
    code: str
    llm_summary: str | None
    issues: list[IssueOut]


class DashboardStats(BaseModel):
    total_scans: int
    average_score: float
    total_issues: int
    severity_counts: dict[str, int]
    category_counts: dict[str, int]
    language_counts: dict[str, int]
    recent_scans: list[ScanSummary]
