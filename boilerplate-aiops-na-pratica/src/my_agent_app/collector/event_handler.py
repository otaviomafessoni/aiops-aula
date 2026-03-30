import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from my_agent_app.models.report import Report

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, sessionmaker: async_sessionmaker) -> None:
        self._sessionmaker = sessionmaker

    async def _get_existing_uids(self, uids: list[str]) -> set[str]:
        async with self._sessionmaker() as session:
            stmt = select(Report.event_uids).where(
                Report.event_uids.overlap(uids),
                Report.status.notin_(["CORRIGIDO"]),
            )
            result = await session.execute(stmt)
            existing = set()
            for (event_uids,) in result:
                existing.update(event_uids)
            return existing

    async def _filter_new_events(self, events: list[dict]) -> list[dict]:
        uids = [e["uid"] for e in events if e.get("uid")]
        if not uids:
            return events

        try:
            existing_uids = await self._get_existing_uids(uids)
        except Exception:
            logger.error("Erro ao consultar banco para deduplicação, aguardando próximo ciclo", exc_info=True)
            return []

        new_events = [e for e in events if e.get("uid") not in existing_uids]

        if len(new_events) < len(events):
            logger.info(
                "Deduplicação: %d/%d eventos já em tratamento",
                len(events) - len(new_events),
                len(events),
            )

        return new_events

    async def _create_report(self, event_uids: list[str]) -> Report:
        async with self._sessionmaker() as session:
            report = Report(
                status="EM_ANALISE",
                event_uids=event_uids,
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            return report

    async def _run_analysis(self, report_id, events: list[dict]) -> None:
        try:
            from my_agent_app.agents.root_cause_agent import analyze_events

            markdown, is_complete = await analyze_events(events)

            async with self._sessionmaker() as session:
                report = await session.get(Report, report_id)
                if report:
                    report.markdown = markdown
                    report.status = "COMPLETO" if is_complete else "INCOMPLETO"
                    await session.commit()

            logger.info("Relatório %s finalizado com status %s", report_id, "COMPLETO" if is_complete else "INCOMPLETO")

            if is_complete:
                try:
                    from my_agent_app.notifications.discord import send_discord_notification

                    lines = [l for l in markdown.strip().splitlines() if l.strip() and not l.strip().startswith("#")]
                    summary = lines[0][:150] if lines else "Sem resumo disponível"
                    await send_discord_notification(str(report_id), summary)
                except Exception:
                    logger.error("Erro ao enviar notificação Discord para relatório %s", report_id, exc_info=True)
        except Exception:
            logger.error("Erro na análise do relatório %s", report_id, exc_info=True)
            try:
                async with self._sessionmaker() as session:
                    report = await session.get(Report, report_id)
                    if report:
                        report.status = "INCOMPLETO"
                        await session.commit()
            except Exception:
                logger.error("Erro ao atualizar status do relatório %s para INCOMPLETO", report_id, exc_info=True)

    async def handle(self, events: list[dict]) -> None:
        new_events = await self._filter_new_events(events)
        if not new_events:
            logger.info("Nenhum evento novo para análise")
            return

        event_uids = [e["uid"] for e in new_events if e.get("uid")]
        report = await self._create_report(event_uids)

        logger.info("Relatório %s criado (EM_ANALISE) com %d eventos", report.id, len(new_events))
        asyncio.create_task(self._run_analysis(report.id, new_events))
