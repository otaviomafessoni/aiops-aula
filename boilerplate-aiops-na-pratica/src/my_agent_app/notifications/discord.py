import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)

DISCORD_API_BASE = "https://discord.com/api/v10"
MAX_RETRIES = 3
BACKOFF_BASE = 1


async def send_discord_notification(report_id: str, summary: str, base_url: str | None = None) -> None:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id = os.environ.get("DISCORD_CHANNEL_ID")

    if not token or not channel_id:
        logger.warning("Variáveis DISCORD_BOT_TOKEN ou DISCORD_CHANNEL_ID não configuradas. Notificação não enviada.")
        return

    if base_url is None:
        base_url = os.environ.get("APP_BASE_URL", "http://localhost:8000")

    report_url = f"{base_url.rstrip('/')}/reports/{report_id}"
    message = (
        f"📋 **Novo relatório de análise gerado**\n\n"
        f"**ID:** {report_id}\n"
        f"**Resumo:** {summary}\n"
        f"**Link:** {report_url}"
    )

    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }
    payload = {"content": message}

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                logger.info("Notificação Discord enviada para relatório %s", report_id)
                return
        except Exception:
            wait = BACKOFF_BASE * (2 ** attempt)
            logger.warning(
                "Falha ao enviar notificação Discord (tentativa %d/%d) para relatório %s. Retry em %ds.",
                attempt + 1,
                MAX_RETRIES,
                report_id,
                wait,
                exc_info=True,
            )
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(wait)

    logger.error("Falha ao enviar notificação Discord após %d tentativas para relatório %s", MAX_RETRIES, report_id)
