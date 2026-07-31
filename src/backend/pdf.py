"""
backend/pdf.py
===============
PDF READINESS SUMMARY.
"""

from __future__ import annotations

import io
from datetime import datetime

import config as C
from .models import PhaseResult


def build_pdf(meta: dict, results: dict[str, PhaseResult], readiness: dict) -> bytes:
    """Render the Readiness Summary as a PDF. Uses reportlab if available,
    otherwise falls back to a minimal hand-built PDF so the download always works."""
    try:
        return _build_pdf_reportlab(meta, results, readiness)
    except Exception:
        lines = _summary_lines(meta, results, readiness)
        return _minimal_pdf(lines)


def _summary_lines(meta, results, readiness) -> list[str]:
    L = [
        C.APP_TITLE,
        "Readiness Summary",
        "",
        f"Assessment : {meta.get('assessment_name','')}",
        f"Assessed by: {meta.get('assessed_by','')}",
        f"Generated  : {datetime.now():%Y-%m-%d %H:%M}",
        "",
    ]
    for phase in C.PHASES:
        r = results.get(phase["id"])
        if not r:
            continue
        L.append(f"{phase['label']}: {r.state}")
        for c in r.checks:
            L.append(f"   - [{c.state}] {c.label}")
    L += ["", "REQUIRED BEFORE WORKS (blocking):"]
    L += [f"   x {c.label}" for c in readiness["blocking"]] or ["   (none)"]
    L += ["", "PENDING ACTIONS (conditional):"]
    L += [f"   ! {c.label}" for c in readiness["pending"]] or ["   (none)"]
    L += ["", "CONFIRMED:"]
    L += [f"   v {c.label}" for c in readiness["confirmed"]] or ["   (none)"]
    L += ["", C.DISCLAIMER]
    L += ["", C.AGWR_BUFFER_ZONE_LIMITATION_NOTE]
    return L


def _build_pdf_reportlab(meta, results, readiness) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    x = 18 * mm
    y = h - 20 * mm

    def line(txt, size=10, colour="#222222", dy=5.4 * mm, bold=False):
        nonlocal y
        if y < 20 * mm:
            c.showPage()
            y = h - 20 * mm
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.setFillColor(HexColor(colour))
        c.drawString(x, y, txt[:110])
        y -= dy

    line(C.APP_TITLE, 15, C.COLOUR_PRIMARY, 7 * mm, bold=True)
    line("Readiness Summary", 12, C.COLOUR_SECONDARY, 7 * mm, bold=True)
    line(f"Assessment: {meta.get('assessment_name','')}")
    line(f"Assessed by: {meta.get('assessed_by','')}    Generated: {datetime.now():%Y-%m-%d %H:%M}")
    y -= 2 * mm

    for phase in C.PHASES:
        r = results.get(phase["id"])
        if not r:
            continue
        gcol = C.STATE_COLOURS.get(r.state, C.COLOUR_NEUTRAL)
        line(f"{phase['label']}  —  {r.state}", 11, gcol, 6 * mm, bold=True)
        for ch in r.checks:
            line(f"   [{ch.state}]  {ch.label}", 9,
                 C.STATE_COLOURS.get(ch.state, C.COLOUR_NEUTRAL))

    y -= 2 * mm
    line("Required before works (blocking):", 10, C.COLOUR_DANGER, bold=True)
    for ch in readiness["blocking"] or []:
        line(f"   x {ch.label}", 9, C.COLOUR_DANGER)
    if not readiness["blocking"]:
        line("   (none)", 9, C.COLOUR_NEUTRAL)
    line("Pending actions:", 10, C.COLOUR_WARNING, bold=True)
    for ch in readiness["pending"] or []:
        line(f"   ! {ch.label}", 9, C.COLOUR_WARNING)
    if not readiness["pending"]:
        line("   (none)", 9, C.COLOUR_NEUTRAL)

    y -= 3 * mm
    c.setFont("Helvetica-Oblique", 7)
    c.setFillColor(HexColor(C.COLOUR_NEUTRAL))
    for chunk in _wrap(C.DISCLAIMER, 130):
        if y < 15 * mm:
            c.showPage(); y = h - 20 * mm
        c.drawString(x, y, chunk); y -= 4 * mm
    y -= 2 * mm
    for chunk in _wrap(C.AGWR_BUFFER_ZONE_LIMITATION_NOTE, 130):
        if y < 15 * mm:
            c.showPage(); y = h - 20 * mm
        c.drawString(x, y, chunk); y -= 4 * mm

    c.showPage()
    c.save()
    return buf.getvalue()


def _wrap(text: str, width: int) -> list[str]:
    out, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > width:
            out.append(cur); cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        out.append(cur)
    return out


def _minimal_pdf(lines: list[str]) -> bytes:
    """Dependency-free fallback PDF (single page, Helvetica 10)."""
    def esc(s):
        return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
    content = "BT /F1 10 Tf 14 TL 40 800 Td\n"
    for ln in lines[:60]:
        content += f"({esc(ln[:110])}) Tj T*\n"
    content += "ET"
    cb = content.encode("latin-1", "replace")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(cb)).encode() + b" >>\nstream\n" + cb + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs)+1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF").encode()
    return out
