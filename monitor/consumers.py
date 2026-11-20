"""
WebSocket consumers for OmniPulse.

MetricsConsumer simulates a fleet of servers emitting telemetry and streams
batched metric snapshots to connected clients once per second. Batching keeps
the frontend from being flooded with individual messages, which is critical
for maintaining 60fps chart rendering under load.
"""

import asyncio
import json
import random
import time
from typing import Any

from channels.generic.websocket import AsyncWebsocketConsumer


# Simulation parameters. Tuned so a single connection produces a realistic
# stream without overwhelming the in-memory channel layer during development.
SIMULATED_SERVERS: list[str] = [
    "edge-eu-west-1",
    "edge-us-east-1",
    "edge-ap-south-1",
    "edge-sa-east-1",
]

METRIC_INTERVAL_SECONDS: float = 2.0   # How often each server emits a sample
BATCH_INTERVAL_SECONDS: float = 1.0    # How often the batch is flushed to client


class MetricsConsumer(AsyncWebsocketConsumer):
    """
    Streams batched infrastructure metrics to a connected WebSocket client.

    Protocol (server -> client), one JSON object per batch:
        {
            "type": "metrics_batch",
            "timestamp": <float unix seconds>,
            "samples": [
                {
                    "server": "<hostname>",
                    "cpu": <float 0-100>,
                    "memory": <float 0-100>,
                    "network_in_kbps": <float>,
                    "network_out_kbps": <float>,
                    "timestamp": <float unix seconds>
                },
                ...
            ]
        }
    """

    async def connect(self) -> None:

        await self.accept()

        self._closed = False
        self._pending_samples: list[dict[str, Any]] = []

        self._producer_task = asyncio.create_task(self._produce_samples())
        self._flusher_task = asyncio.create_task(self._flush_batches())

    async def disconnect(self, close_code: int) -> None:
        self._closed = True
        for task in (self._producer_task, self._flusher_task):
            task.cancel()
        # Wait for cancellation to propagate so no warnings leak into logs.
        for task in (self._producer_task, self._flusher_task):
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if payload.get("type") == "ping":
            await self.send(json.dumps({"type": "pong", "timestamp": time.time()}))

    
    # Internal tasks

    async def _produce_samples(self) -> None:
        """
        Emits one sample per simulated server every METRIC_INTERVAL_SECONDS and
        appends it to the pending buffer. The flusher task drains the buffer.
        """
        while not self._closed:
            now = time.time()
            for server in SIMULATED_SERVERS:
                self._pending_samples.append(
                    {
                        "server": server,
                        "cpu": round(random.uniform(5.0, 95.0), 2),
                        "memory": round(random.uniform(10.0, 90.0), 2),
                        "network_in_kbps": round(random.uniform(50.0, 5000.0), 2),
                        "network_out_kbps": round(random.uniform(50.0, 5000.0), 2),
                        "timestamp": now,
                    }
                )
            await asyncio.sleep(METRIC_INTERVAL_SECONDS)

    async def _flush_batches(self) -> None:
        """
        Drains pending samples once per BATCH_INTERVAL_SECONDS and sends them as
        a single frame. This is the key optimisation: the client receives one
        message per second regardless of how many servers or samples exist.
        """
        while not self._closed:
            await asyncio.sleep(BATCH_INTERVAL_SECONDS)
            if not self._pending_samples:
                continue

            batch = self._pending_samples
            self._pending_samples = []

            try:
                await self.send(
                    json.dumps(
                        {
                            "type": "metrics_batch",
                            "timestamp": time.time(),
                            "samples": batch,
                        }
                    )
                )
            except Exception:
                # Connection likely dropped between flusher and send; let the
                # disconnect handler clean up.
                self._closed = True
                return
            