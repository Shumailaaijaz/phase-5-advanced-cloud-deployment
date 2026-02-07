"""Event Transport Abstraction

Dual transport: Dapr HTTP (localhost:3500) or direct aiokafka.
Controlled by USE_DAPR environment variable.
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

DAPR_URL = "http://localhost:3500/v1.0/publish/task-pubsub"
USE_DAPR = os.getenv("USE_DAPR", "true").lower() == "true"


class DaprTransport:
    """Publish events via Dapr HTTP sidecar."""

    async def publish(self, topic: str, event: Dict[str, Any]) -> bool:
        import httpx
        url = f"{DAPR_URL}/{topic}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    json=event,
                    headers={"Content-Type": "application/json"},
                    timeout=5.0,
                )
                resp.raise_for_status()
                logger.info(f"Event published via Dapr to {topic}: {event.get('event_type', 'unknown')}")
                return True
        except Exception as e:
            logger.warning(f"Dapr publish failed for {topic}: {e}")
            return False


class KafkaTransport:
    """Publish events directly via aiokafka (fallback when Dapr unavailable)."""

    def __init__(self):
        self._producer = None

    async def _get_producer(self):
        if self._producer is None:
            from aiokafka import AIOKafkaProducer
            brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
            self._producer = AIOKafkaProducer(
                bootstrap_servers=brokers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
        return self._producer

    async def publish(self, topic: str, event: Dict[str, Any]) -> bool:
        try:
            producer = await self._get_producer()
            await producer.send_and_wait(topic, event)
            logger.info(f"Event published via Kafka to {topic}: {event.get('event_type', 'unknown')}")
            return True
        except Exception as e:
            logger.warning(f"Kafka publish failed for {topic}: {e}")
            return False


def get_transport():
    """Factory: returns DaprTransport if USE_DAPR=true, else KafkaTransport."""
    if USE_DAPR:
        return DaprTransport()
    return KafkaTransport()
