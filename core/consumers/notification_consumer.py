"""
core/consumers/notification_consumer.py
-----------------------------------------
WebSocket consumer for real-time notifications.

Architecture:
  - Each user gets their own notification group: notif_user_{user_id}
  - On connect: join personal notification group
  - Server pushes new notifications via group_send from views/signals
  - Client receives and updates notification badge without polling
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

    class NotificationConsumer(AsyncWebsocketConsumer):
        """
        Personal notification channel per authenticated user.
        URL pattern: ws/notifications/
        """

        async def connect(self):
            self.user = self.scope['user']
            if not self.user.is_authenticated:
                await self.close()
                return

            self.group_name = f"notif_user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

            # Send unread count on connect
            count = await self._get_unread_count()
            await self.send(text_data=json.dumps({
                'type':         'unread_count',
                'unread_count': count,
            }))

        async def disconnect(self, close_code):
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(self.group_name, self.channel_name)

        async def receive(self, text_data):
            """Client can request 'mark_read' via WebSocket."""
            try:
                data = json.loads(text_data)
                if data.get('type') == 'mark_read':
                    await self._mark_all_read()
                    await self.send(text_data=json.dumps({'type': 'marked_read'}))
            except json.JSONDecodeError:
                pass

        async def notify(self, event):
            """Push a new notification to the client."""
            await self.send(text_data=json.dumps({
                'type':    'notification',
                'message': event.get('message', ''),
                'notif_type': event.get('notif_type', ''),
                'sender':  event.get('sender', ''),
            }))

        @database_sync_to_async  # type: ignore[name-defined]
        def _get_unread_count(self) -> int:
            from core.services.notification_service import get_unread_count
            return get_unread_count(self.user)

        @database_sync_to_async  # type: ignore[name-defined]
        def _mark_all_read(self):
            from core.services.notification_service import mark_all_read
            mark_all_read(self.user)

    # Fix missing import inside class body
    from channels.db import database_sync_to_async
    NotificationConsumer._get_unread_count = database_sync_to_async(
        NotificationConsumer._get_unread_count.__wrapped__
        if hasattr(NotificationConsumer._get_unread_count, '__wrapped__')
        else NotificationConsumer._get_unread_count
    )

else:

    class NotificationConsumer:
        """Stub when channels is not installed."""
        pass
