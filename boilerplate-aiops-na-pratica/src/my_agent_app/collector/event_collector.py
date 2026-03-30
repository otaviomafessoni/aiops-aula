import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from my_agent_app.collector.event_handler import EventHandler

logger = logging.getLogger(__name__)

CLOCK_DRIFT_MARGIN_SECONDS = 10


class EventCollector:
    def __init__(self, handler: EventHandler, interval_minutes: int = 3) -> None:
        self._handler = handler
        self._interval_minutes = interval_minutes
        self._load_kube_config()

    def _load_kube_config(self) -> None:
        try:
            config.load_incluster_config()
            logger.info("Autenticação in-cluster configurada")
        except config.ConfigException:
            config.load_kube_config()
            logger.info("Autenticação via kubeconfig local configurada")

    def _collect_events(self) -> list[dict]:
        api = client.CoreV1Api()
        resp = api.list_event_for_all_namespaces(
            field_selector="type=Warning",
            _preload_content=False,
        )
        data = json.loads(resp.data)
        return data.get("items", [])

    def _parse_timestamp(self, ts_str: str | None) -> datetime | None:
        if not ts_str:
            return None
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def _get_event_timestamp(self, event: dict) -> datetime | None:
        for field in ("eventTime", "deprecatedLastTimestamp", "lastTimestamp", "firstTimestamp"):
            ts = self._parse_timestamp(event.get(field))
            if ts is not None:
                return ts
        return None

    def _filter_by_time(self, events: list[dict], cutoff: datetime) -> list[dict]:
        filtered = []
        for event in events:
            ts = self._get_event_timestamp(event)
            if ts is None:
                metadata = event.get("metadata", {})
                logger.warning(
                    "Evento %s descartado: sem eventTime ou deprecatedLastTimestamp",
                    metadata.get("uid", "unknown"),
                )
                continue
            if ts >= cutoff:
                filtered.append(event)
        return filtered

    def _transform_event(self, event: dict) -> dict:
        ts = self._get_event_timestamp(event)
        metadata = event.get("metadata", {})
        involved = event.get("involvedObject") or event.get("regarding") or {}
        message = event.get("message") or event.get("note")
        return {
            "uid": metadata.get("uid"),
            "type": "Warning",
            "reason": event.get("reason"),
            "message": message,
            "namespace": metadata.get("namespace"),
            "involved_object": {
                "kind": involved.get("kind"),
                "name": involved.get("name"),
                "namespace": involved.get("namespace"),
            },
            "timestamp": ts.isoformat() if ts else None,
        }

    async def _collect_and_handle(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=self._interval_minutes,
            seconds=CLOCK_DRIFT_MARGIN_SECONDS,
        )

        raw_events = await asyncio.to_thread(self._collect_events)
        events = self._filter_by_time(raw_events, cutoff)

        if not events:
            logger.info("Nenhum evento Warning no intervalo")
            return

        transformed = [self._transform_event(e) for e in events]
        logger.info("Coletados %d eventos Warning", len(transformed))
        await self._handler.handle(transformed)

    async def run(self) -> None:
        logger.info("EventCollector iniciado (intervalo: %d min)", self._interval_minutes)
        while True:
            try:
                await self._collect_and_handle()
            except ApiException as e:
                logger.error("Erro na API Kubernetes (status %s): %s", e.status, e.reason)
            except ConnectionError as e:
                logger.error("Erro de conexão com o cluster: %s", e)
            except Exception as e:
                logger.error("Erro inesperado na coleta: %s", e)
            await asyncio.sleep(self._interval_minutes * 60)
