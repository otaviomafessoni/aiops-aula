import asyncio
import logging
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from my_agent_app.agents.fix_agent import execute_fix
from my_agent_app.models.report import Report
from my_agent_app.notifications.discord import send_discord_notification

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/health")
def health():
    return {"status": "ok"}


async def _get_session(request: Request) -> AsyncSession:
    sessionmaker = request.app.state.sessionmaker
    return sessionmaker()


async def _run_fix(sessionmaker, report_id: uuid.UUID, report_markdown: str):
    """Task background que executa o agente de correção."""
    try:
        fix_result, status = await execute_fix(report_markdown)
    except Exception:
        logger.exception("Exceção não tratada durante correção do relatório %s", report_id)
        fix_result = "Erro: exceção não tratada durante a execução do agente de correção"
        status = "FALHA_CORRECAO"

    session = sessionmaker()
    try:
        async with session:
            report = await session.get(Report, report_id)
            if report:
                report.fix_result = fix_result
                report.status = status
                await session.commit()
                logger.info("Relatório %s atualizado com status %s", report_id, status)
    except Exception:
        logger.exception("Erro ao persistir resultado da correção para relatório %s", report_id)

    first_line = fix_result.strip().split("\n")[0] if fix_result else "Sem detalhes"
    summary = f"Correção {'bem-sucedida' if status == 'CORRIGIDO' else 'com falha'}: {first_line}"
    try:
        await send_discord_notification(str(report_id), summary)
    except Exception:
        logger.exception("Erro ao enviar notificação Discord para relatório %s", report_id)


@router.post("/api/reports/{report_id}/fix")
async def fix_report(request: Request, report_id: uuid.UUID):
    session = await _get_session(request)
    async with session:
        report = await session.get(Report, report_id)

        if not report:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Relatório não encontrado"},
            )

        if report.status != "COMPLETO":
            return JSONResponse(
                status_code=409,
                content={
                    "status": "error",
                    "message": f"Relatório com status '{report.status}' não pode ser corrigido. Status esperado: COMPLETO",
                },
            )

        report.status = "CORRIGINDO"
        await session.commit()

    sessionmaker = request.app.state.sessionmaker
    asyncio.create_task(_run_fix(sessionmaker, report_id, report.markdown))

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "message": "Correção iniciada"},
    )
