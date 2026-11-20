import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("metrics", self.channel_name)
        await self.accept()
        self._closed = False

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("metrics", self.channel_name)
        self._closed = True

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def metrics_message(self, event):
        samples = event["samples"]
        await self.send(
            json.dumps({
                "type": "metrics_batch",
                "samples": samples,
            })
        )
        