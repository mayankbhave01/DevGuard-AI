from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.scan import Scan, Issue
from app.schemas.scan import ScanCreate, ScanDetail, ScanSummary, DashboardStats
from app.services.analyzer import analyze_code
from app.services.llm import enhance_review
from app.services.reports import (
    ReportOptions,
    bundle_report,
    csv_report,
    html_report,
    json_report,
    markdown_report,
    pdf_report,
    text_report,
)

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("", response_model=ScanDetail, status_code=201)
async def create_scan(payload: ScanCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    analysis = analyze_code(payload.code, payload.language)
    llm_summary = None
    if payload.use_llm:
        llm_summary = await enhance_review(payload.code, payload.language, analysis["findings"])

    counts = analysis["counts"]
    scan = Scan(
        user_id=user.id,
        title=payload.title.strip() or "Untitled scan",
        language=payload.language.lower(),
        code=payload.code,
        score=analysis["score"],
        issue_count=len(analysis["findings"]),
        critical_count=counts.get("critical", 0),
        high_count=counts.get("high", 0),
        medium_count=counts.get("medium", 0),
        low_count=counts.get("low", 0),
        llm_summary=llm_summary,
    )
    db.add(scan)
    db.flush()
    for item in analysis["findings"]:
        db.add(Issue(scan_id=scan.id, **item))
    db.commit()
    db.refresh(scan)
    return scan


@router.get("", response_model=list[ScanSummary])
def list_scans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Scan).filter(Scan.user_id == user.id).order_by(Scan.created_at.desc()).all()


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scans = db.query(Scan).filter(Scan.user_id == user.id).order_by(Scan.created_at.desc()).all()
    issue_rows = db.query(Issue).join(Scan, Issue.scan_id == Scan.id).filter(Scan.user_id == user.id).all()
    severity = Counter(i.severity for i in issue_rows)
    categories = Counter(i.category for i in issue_rows)
    languages = Counter(s.language for s in scans)
    avg = round(sum(s.score for s in scans) / len(scans), 1) if scans else 0.0
    return DashboardStats(
        total_scans=len(scans),
        average_score=avg,
        total_issues=len(issue_rows),
        severity_counts=dict(severity),
        category_counts=dict(categories),
        language_counts=dict(languages),
        recent_scans=scans[:5],
    )


@router.get("/{scan_id}", response_model=ScanDetail)
def get_scan(scan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.delete("/{scan_id}", status_code=204)
def delete_scan(scan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    db.delete(scan)
    db.commit()
    return Response(status_code=204)


@router.get("/{scan_id}/export/{fmt}")
def export_scan(
    scan_id: int,
    fmt: str,
    include_source: bool = True,
    include_suggestions: bool = True,
    include_summary: bool = True,
    mode: str = "detailed",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if mode not in {"summary", "detailed"}:
        raise HTTPException(status_code=400, detail="mode must be summary or detailed")

    options = ReportOptions(
        include_source=include_source,
        include_suggestions=include_suggestions,
        include_summary=include_summary,
        mode=mode,
    )
    fmt = fmt.lower()
    exporters = {
        "json": (lambda: json_report(scan, options), "application/json; charset=utf-8", "json"),
        "md": (lambda: markdown_report(scan, options), "text/markdown; charset=utf-8", "md"),
        "markdown": (lambda: markdown_report(scan, options), "text/markdown; charset=utf-8", "md"),
        "txt": (lambda: text_report(scan, options), "text/plain; charset=utf-8", "txt"),
        "csv": (lambda: csv_report(scan, options), "text/csv; charset=utf-8", "csv"),
        "html": (lambda: html_report(scan, options), "text/html; charset=utf-8", "html"),
        "pdf": (lambda: pdf_report(scan, options), "application/pdf", "pdf"),
        "zip": (lambda: bundle_report(scan, options), "application/zip", "zip"),
        "all": (lambda: bundle_report(scan, options), "application/zip", "zip"),
    }
    if fmt not in exporters:
        raise HTTPException(status_code=400, detail="Supported formats: pdf, html, md, json, csv, txt, zip")

    build, media, extension = exporters[fmt]
    content = build()
    filename = f"devguard-scan-{scan.id}.{extension}"
    return Response(content=content, media_type=media, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
