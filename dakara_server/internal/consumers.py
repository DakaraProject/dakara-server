from channels.generic.websocket import WebsocketConsumer


class HeartbeatConsumer(WebsocketConsumer):
    """Consumer for heartbeats."""

    def connect(self):
        # accept all connections
        self.accept()
