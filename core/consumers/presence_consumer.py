"""
core/consumers/presence_consumer.py
-------------------------------------
WebSocket consumer for online/offline presence tracking.

Architecture:
  - All clients join the shared 'presence' group
  - On connect: broadcast user came online
  - On disconnect: broadcast user went offline
  - Can be extended with typing indicators, seen receipts
"""

import json
import logging

logger = logging.getLogger(__name__)

try:
    from channels.generic.websocket import AsyncWebsocketConsumer
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
    class AsyncWebsocketConsumer:
        pass


if CHANNELS_AVAILABLE:

    class PresenceConsumer(AsyncWebsocketConsumer):
        """
        Tracks online/offline status for authenticated users.
        URL pattern: ws/presence/
        """

        PRESENCE_GROUP = 'presence'

        async def connect(self):
            self.user = self.scope['user']
            if not self.user.is_authenticated:
                await self.close()
                return

            await self.channel_layer.group_add(self.PRESENCE_GROUP, self.channel_name)
            await self.accept()

            # Announce online
            await self.channel_layer.group_send(
                self.PRESENCE_GROUP,
                {
                    'type':    'presence_update',
                    'user_id': self.user.id,
                    'status':  'online',
                },
            )

        async def disconnect(self, close_code):
            if not hasattr(self, 'user') or not self.user.is_authenticated:
                return

            # Announce offline
            await self.channel_layer.group_send(
                self.PRESENCE_GROUP,
                {
                    'type':    'presence_update',
                    'user_id': self.user.id,
                    'status':  'offline',
                },
            )
            await self.channel_layer.group_discard(self.PRESENCE_GROUP, self.channel_name)

        async def receive(self, text_data):
            """Handle typing indicator events from client."""
            try:
                data = json.loads(text_data)
                event_type = data.get('type')
                if event_type in ('typing_start', 'typing_stop'):
                    await self.channel_layer.group_send(
                        f"chat_{data.get('conversation_id')}",
                        {
                            'type':    'typing_event',
                            'user_id': self.user.id,
                            'status':  event_type,
                        },
                    )
            except json.JSONDecodeError:
                pass

        async def presence_update(self, event):
            """Relay presence update to this client."""
            await self.send(text_data=json.dumps({
                'type':    'presence',
                'user_id': event['user_id'],
                'status':  event['status'],
            }))

        async def typing_event(self, event):
            """Relay typing indicator to this client."""
            await self.send(text_data=json.dumps({
                'type':    event['status'],
                'user_id': event['user_id'],
            }))

else:

    class PresenceConsumer:
        """Stub when channels is not installed."""
        pass
