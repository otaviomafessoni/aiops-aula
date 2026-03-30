import uuid
from pathlib import Path

import markdown
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from my_agent_app.models.report import Report

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

STATUS_BADGE_MAP = {
    "EM_ANALISE": "badge-processing",
    "COMPLETO": "badge-complete",
    "INCOMPLETO": "badge-incomplete",
    "CORRIGINDO": "badge-executing",
    "CORRIGIDO": "badge-executed",
    "FALHA_CORRECAO": "badge-execution-failed",
}


async def _get_session(request: Request) -> AsyncSession:
    sessionmaker = request.app.state.sessionmaker
    return sessionmaker()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/reports", status_code=302)


@router.get("/reports", response_class=HTMLResponse)
async def reports_list(request: Request):
    try:
        session = await _get_session(request)
        async with session:
            stmt = select(Report).order_by(Report.created_at.desc())
            result = await session.execute(stmt)
            reports = result.scalars().all()
    except Exception:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"status_code": 500, "message": "Erro ao conectar com o banco de dados. Tente novamente mais tarde."},
            status_code=500,
        )

    reports_data = []
    for r in reports:
        summary = ""
        if r.markdown:
            lines = [l for l in r.markdown.strip().splitlines() if l.strip() and not l.strip().startswith("#")]
            summary = lines[0][:150] if lines else ""
        reports_data.append({
            "id": r.id,
            "created_at": r.created_at,
            "status": r.status,
            "badge_class": STATUS_BADGE_MAP.get(r.status, "badge-processing"),
            "summary": summary,
        })

    return templates.TemplateResponse(
        request,
        "reports_list.html",
        {"reports": reports_data},
    )


@router.get("/reports/{report_id}", response_class=HTMLResponse)
async def report_detail(request: Request, report_id: uuid.UUID):
    try:
        session = await _get_session(request)
        async with session:
            report = await session.get(Report, report_id)
    except Exception:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"status_code": 500, "message": "Erro ao conectar com o banco de dados. Tente novamente mais tarde."},
            status_code=500,
        )

    if not report:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"status_code": 404, "message": "Relatório não encontrado."},
            status_code=404,
        )

    md = markdown.Markdown(extensions=["tables", "fenced_code"])
    html_content = md.convert(report.markdown or "")

    fix_html_content = None
    if report.fix_result:
        md_fix = markdown.Markdown(extensions=["tables", "fenced_code"])
        fix_html_content = md_fix.convert(report.fix_result)

    return templates.TemplateResponse(
        request,
        "report_detail.html",
        {
            "report": report,
            "html_content": html_content,
            "fix_html_content": fix_html_content,
            "badge_class": STATUS_BADGE_MAP.get(report.status, "badge-processing"),
        },
    )
