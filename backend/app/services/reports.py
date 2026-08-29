from __future__ import annotations

import csv
import html
import io
import json
import zipfile
from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.scan import Scan


@dataclass(slots=True)
class ReportOptions:
    include_source: bool = True
    include_suggestions: bool = True
    include_summary: bool = True
    mode: str = "detailed"

    @property
    def detailed(self) -> bool:
        return self.mode != "summary"


def scan_to_dict(scan: Scan, options: ReportOptions | None = None) -> dict:
    options = options or ReportOptions()
    data = {
        "id": scan.id,
        "title": scan.title,
        "language": scan.language,
        "score": scan.score,
        "issue_count": scan.issue_count,
        "critical_count": scan.critical_count,
        "high_count": scan.high_count,
        "medium_count": scan.medium_count,
        "low_count": scan.low_count,
        "created_at": scan.created_at.isoformat(),
        "report_mode": options.mode,
        "issues": [],
    }
    if options.include_summary:
        data["llm_summary"] = scan.llm_summary
    if options.include_source:
        data["source_code"] = scan.code

    for i in scan.issues:
        item = {
            "rule_id": i.rule_id,
            "category": i.category,
            "severity": i.severity,
            "title": i.title,
            "line": i.line,
        }
        if options.detailed:
            item["description"] = i.description
            item["snippet"] = i.snippet
        if options.include_suggestions:
            item["suggestion"] = i.suggestion
        data["issues"].append(item)
    return data


def json_report(scan: Scan, options: ReportOptions | None = None) -> str:
    return json.dumps(scan_to_dict(scan, options), indent=2, ensure_ascii=False)


def markdown_report(scan: Scan, options: ReportOptions | None = None) -> str:
    options = options or ReportOptions()
    lines = [
        f"# DevGuard AI Report — {scan.title}",
        "",
        f"- Language: **{scan.language}**",
        f"- Code health score: **{scan.score}/100**",
        f"- Issues: **{scan.issue_count}**",
        f"- Created: **{scan.created_at.isoformat()}**",
        f"- Report mode: **{options.mode.title()}**",
        "",
        "## Severity Summary",
        "",
        f"- Critical: {scan.critical_count}",
        f"- High: {scan.high_count}",
        f"- Medium: {scan.medium_count}",
        f"- Low: {scan.low_count}",
        "",
    ]
    if options.include_summary and scan.llm_summary:
        lines += ["## AI Summary", "", scan.llm_summary, ""]

    lines += ["## Findings", ""]
    for issue in scan.issues:
        lines += [
            f"### [{issue.severity.upper()}] {issue.title}",
            "",
            f"- Rule: `{issue.rule_id}`",
            f"- Category: `{issue.category}`",
            f"- Line: {issue.line or 'N/A'}",
        ]
        if options.detailed:
            lines += [f"- Description: {issue.description}"]
            if issue.snippet:
                lines += ["", "```", issue.snippet, "```"]
        if options.include_suggestions:
            lines += [f"- Suggested fix: {issue.suggestion}"]
        lines += [""]

    if options.include_source:
        lines += ["## Reviewed Source", "", f"```{scan.language}", scan.code, "```", ""]
    return "\n".join(lines)


def text_report(scan: Scan, options: ReportOptions | None = None) -> str:
    options = options or ReportOptions()
    parts = [
        "DEVGUARD AI SECURITY & QUALITY REPORT",
        "=" * 44,
        f"Title: {scan.title}",
        f"Language: {scan.language}",
        f"Code health score: {scan.score}/100",
        f"Issues: {scan.issue_count}",
        f"Created: {scan.created_at.isoformat()}",
        "",
        f"Severity: Critical {scan.critical_count} | High {scan.high_count} | Medium {scan.medium_count} | Low {scan.low_count}",
        "",
        "FINDINGS",
        "-" * 44,
    ]
    for idx, issue in enumerate(scan.issues, 1):
        parts += [
            f"{idx}. [{issue.severity.upper()}] {issue.title}",
            f"   Rule: {issue.rule_id} | Category: {issue.category} | Line: {issue.line or 'N/A'}",
        ]
        if options.detailed:
            parts += [f"   Description: {issue.description}"]
            if issue.snippet:
                parts += [f"   Code: {issue.snippet}"]
        if options.include_suggestions:
            parts += [f"   Suggested fix: {issue.suggestion}"]
        parts += [""]
    if options.include_summary and scan.llm_summary:
        parts += ["AI SUMMARY", "-" * 44, scan.llm_summary, ""]
    if options.include_source:
        parts += ["REVIEWED SOURCE", "-" * 44, scan.code, ""]
    return "\n".join(parts)


def csv_report(scan: Scan, options: ReportOptions | None = None) -> str:
    options = options or ReportOptions()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    header = ["scan_id", "scan_title", "language", "score", "rule_id", "severity", "category", "line", "finding"]
    if options.detailed:
        header += ["description", "snippet"]
    if options.include_suggestions:
        header += ["suggested_fix"]
    writer.writerow(header)
    for issue in scan.issues:
        row = [scan.id, scan.title, scan.language, scan.score, issue.rule_id, issue.severity, issue.category, issue.line or "", issue.title]
        if options.detailed:
            row += [issue.description, issue.snippet or ""]
        if options.include_suggestions:
            row += [issue.suggestion]
        writer.writerow(row)
    return output.getvalue()


def html_report(scan: Scan, options: ReportOptions | None = None) -> str:
    options = options or ReportOptions()
    severity_rows = "".join(
        f"<div class='stat'><span>{label}</span><strong>{value}</strong></div>"
        for label, value in [
            ("Critical", scan.critical_count),
            ("High", scan.high_count),
            ("Medium", scan.medium_count),
            ("Low", scan.low_count),
        ]
    )
    findings = []
    for issue in scan.issues:
        detail = f"<p>{html.escape(issue.description)}</p>" if options.detailed else ""
        snippet = f"<pre>{html.escape(issue.snippet)}</pre>" if options.detailed and issue.snippet else ""
        suggestion = (
            f"<div class='fix'><b>Suggested fix</b><p>{html.escape(issue.suggestion)}</p></div>"
            if options.include_suggestions
            else ""
        )
        findings.append(
            f"""
            <article class='finding'>
              <div class='meta'><span class='badge {html.escape(issue.severity)}'>{html.escape(issue.severity.upper())}</span>
              <span>{html.escape(issue.rule_id)}</span><span>{html.escape(issue.category)}</span><span>Line {issue.line or 'N/A'}</span></div>
              <h3>{html.escape(issue.title)}</h3>{detail}{snippet}{suggestion}
            </article>
            """
        )
    summary = ""
    if options.include_summary and scan.llm_summary:
        summary = f"<section><h2>AI Summary</h2><p>{html.escape(scan.llm_summary)}</p></section>"
    source = ""
    if options.include_source:
        source = f"<section><h2>Reviewed Source</h2><pre>{html.escape(scan.code)}</pre></section>"

    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>DevGuard AI Report — {html.escape(scan.title)}</title>
<style>
body{{font-family:Inter,Segoe UI,Arial,sans-serif;background:#07101f;color:#e8edf7;margin:0;padding:36px;line-height:1.55}}
.wrap{{max-width:980px;margin:auto}} .hero,.finding,section{{background:#0e1a2e;border:1px solid #243654;border-radius:16px;padding:22px;margin:16px 0}}
.eyebrow{{color:#74a3ff;font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}} h1{{margin:.2em 0;font-size:34px}} h2{{font-size:19px}}
.score{{font-size:42px;font-weight:800;background:linear-gradient(90deg,#6ea8ff,#8b5cf6);-webkit-background-clip:text;color:transparent}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:18px}} .stat{{background:#081324;border:1px solid #1f3352;padding:14px;border-radius:12px}} .stat span{{color:#91a2bf;display:block;font-size:12px}} .stat strong{{font-size:22px}}
.meta{{display:flex;gap:9px;flex-wrap:wrap;color:#91a2bf;font-size:12px}} .badge{{font-size:10px;font-weight:800;padding:4px 8px;border-radius:999px}} .critical{{background:#5b1822;color:#ff9da8}} .high{{background:#5b2c11;color:#ffb071}} .medium{{background:#54410d;color:#f7d55f}} .low{{background:#123958;color:#7ed1ff}}
pre{{white-space:pre-wrap;overflow:auto;background:#050c17;border:1px solid #1b2a43;border-radius:10px;padding:14px;color:#c7d5ed}} .fix{{border-left:3px solid #5b8cff;padding-left:14px;margin-top:14px}} footer{{color:#71829f;text-align:center;margin-top:32px;font-size:12px}}
@media(max-width:700px){{body{{padding:16px}}.stats{{grid-template-columns:1fr 1fr}}}}
</style></head><body><div class='wrap'>
<div class='hero'><div class='eyebrow'>DevGuard AI • Security & Quality Intelligence</div><h1>{html.escape(scan.title)}</h1>
<p>{html.escape(scan.language)} • {html.escape(scan.created_at.isoformat())} • {html.escape(options.mode.title())} report</p>
<div class='score'>{scan.score}/100</div><div class='stats'>{severity_rows}</div></div>
{summary}<section><h2>Findings ({scan.issue_count})</h2>{''.join(findings)}</section>{source}
<footer>Generated by DevGuard AI</footer></div></body></html>"""


def pdf_report(scan: Scan, options: ReportOptions | None = None) -> bytes:
    options = options or ReportOptions()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"DevGuard AI Report - {scan.title}",
        author="DevGuard AI",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DGTitle", parent=styles["Title"], textColor=colors.HexColor("#13213A"), fontSize=22, leading=26, alignment=TA_LEFT)
    h2 = ParagraphStyle("DGH2", parent=styles["Heading2"], textColor=colors.HexColor("#1D4ED8"), fontSize=14, spaceBefore=10, spaceAfter=7)
    body = ParagraphStyle("DGBody", parent=styles["BodyText"], textColor=colors.HexColor("#334155"), fontSize=9.5, leading=14)
    small = ParagraphStyle("DGSmall", parent=body, fontSize=8, textColor=colors.HexColor("#64748B"))
    mono = ParagraphStyle("DGMono", fontName="Courier", fontSize=7.3, leading=9, textColor=colors.HexColor("#0F172A"), backColor=colors.HexColor("#F1F5F9"), borderPadding=7)

    story = [
        Paragraph("DEVGUARD AI • SECURITY &amp; QUALITY REPORT", small),
        Paragraph(html.escape(scan.title), title_style),
        Paragraph(f"Language: <b>{html.escape(scan.language)}</b> &nbsp;&nbsp; | &nbsp;&nbsp; Created: {html.escape(scan.created_at.isoformat())}", body),
        Spacer(1, 8),
    ]
    summary_table = Table(
        [
            ["Code health", "Total issues", "Critical", "High", "Medium", "Low"],
            [f"{scan.score}/100", str(scan.issue_count), str(scan.critical_count), str(scan.high_count), str(scan.medium_count), str(scan.low_count)],
        ],
        colWidths=[30 * mm, 30 * mm, 24 * mm, 24 * mm, 24 * mm, 24 * mm],
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0FF")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#475569")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#0F172A")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [summary_table, Spacer(1, 12)]

    if options.include_summary and scan.llm_summary:
        story += [Paragraph("AI Summary", h2), Paragraph(html.escape(scan.llm_summary), body)]

    story += [Paragraph(f"Findings ({scan.issue_count})", h2)]
    for idx, issue in enumerate(scan.issues, 1):
        sev_color = {"critical": "#B91C1C", "high": "#C2410C", "medium": "#A16207", "low": "#0369A1"}.get(issue.severity, "#475569")
        story += [
            Paragraph(f"<font color='{sev_color}'><b>{idx}. [{html.escape(issue.severity.upper())}] {html.escape(issue.title)}</b></font>", body),
            Paragraph(f"Rule: <b>{html.escape(issue.rule_id)}</b> &nbsp; • &nbsp; Category: {html.escape(issue.category)} &nbsp; • &nbsp; Line: {issue.line or 'N/A'}", small),
        ]
        if options.detailed:
            story += [Paragraph(html.escape(issue.description), body)]
            if issue.snippet:
                story += [Preformatted(issue.snippet, mono)]
        if options.include_suggestions:
            story += [Paragraph(f"<b>Suggested fix:</b> {html.escape(issue.suggestion)}", body)]
        story += [Spacer(1, 8)]

    if options.include_source:
        story += [PageBreak(), Paragraph("Reviewed Source", h2), Preformatted(scan.code, mono)]

    doc.build(story)
    return buffer.getvalue()


def bundle_report(scan: Scan, options: ReportOptions | None = None) -> bytes:
    options = options or ReportOptions()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        base = f"devguard-scan-{scan.id}"
        zf.writestr(f"{base}.json", json_report(scan, options).encode("utf-8"))
        zf.writestr(f"{base}.md", markdown_report(scan, options).encode("utf-8"))
        zf.writestr(f"{base}.txt", text_report(scan, options).encode("utf-8"))
        zf.writestr(f"{base}.csv", csv_report(scan, options).encode("utf-8-sig"))
        zf.writestr(f"{base}.html", html_report(scan, options).encode("utf-8"))
        zf.writestr(f"{base}.pdf", pdf_report(scan, options))
    return buffer.getvalue()
