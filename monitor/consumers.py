import asyncio
import json
import random
import time
from typing import Any
from channels.generic.websocket import AsyncWebsocketConsumer

SIMULATED_SERVERS = ["edge-eu-west-1", "edge-us-east-1", "edge-ap-south-1", "edge-sa-east-1"]
METRIC_INTERVAL_SECONDS = 2.0
BATCH_INTERVAL_SECONDS = 1.0

class MetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("metrics", self.channel_name)
        await self.accept()
        self._closed = False
        self._pending_samples = []
        
        self._producer_task = asyncio.create_task(self._produce_samples())
        self._flusher_task = asyncio.create_task(self._flush_batches())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("metrics", self.channel_name)
        self._closed = True
        for task in (self._producer_task, self._flusher_task):
            task.cancel()
        for task in (self._producer_task, self._flusher_task):
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return
        if payload.get("type") == "ping":
            await self.send(json.dumps({"type": "pong", "timestamp": time.time()}))

    async def metrics_message(self, event):
        samples = event["samples"]
        await self.send(
            json.dumps({
                "type": "metrics_batch",
                "timestamp": time.time(),
                "samples": samples,
            })
        )

    async def _produce_samples(self):
        while not self._closed:
            now = time.time()
            for server in SIMULATED_SERVERS:
                self._pending_samples.append({
                    "server": server,
                    "cpu": round(random.uniform(5.0, 95.0), 2),
                    "memory": round(random.uniform(10.0, 90.0), 2),
                    "network_in_kbps": round(random.uniform(50.0, 5000.0), 2),
                    "network_out_kbps": round(random.uniform(50.0, 5000.0), 2),
                    "timestamp": now,
                })
            await asyncio.sleep(METRIC_INTERVAL_SECONDS)

    async def _flush_batches(self):
        while not self._closed:
            await asyncio.sleep(BATCH_INTERVAL_SECONDS)
            if not self._pending_samples:
                continue
            batch = self._pending_samples
            self._pending_samples = []
            try:
                await self.send(json.dumps({
                    "type": "metrics_batch",
                    "timestamp": time.time(),
                    "samples": batch,
                }))
            except Exception:
                self._closed = True
                return
            