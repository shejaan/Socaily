"""
core/consumers/chat_consumer.py
---------------------------------
WebSocket consumer for real-time direct messaging.

Architecture:
  - Each conversation gets its own channel group: chat_{conversation_id}
  - On connect: join group, mark messages read
  - On receive: save Message to DB, broadcast to group
  - On disconnect: leave group

Requires:
  - channels>=4.0
  - channels-redis
  - Redis channel layer configured in settings.py
"""

import json
import logging

logger = logging.getLogger(__name__)

try:
    from channels.generic.websocket import AsyncWebsocketConsumer
    from channels.db import database_sync_to_async
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
    # Stub so the module imports cleanly even without channels installed
    class AsyncWebsocketConsumer:
        pass


if CHANNELS_AVAILABLE:

    class ChatConsumer(AsyncWebsocketConsumer):
        """
        Handles WebSocket connections for a single conversation.
        URL pattern: ws/chat/<conversation_id>/
        """

        async def connect(self):
            self.user = self.scope['user']
            if not self.user.is_authenticated:
                await self.close()
                return

            self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
            self.room_group_name = f"chat_{self.conversation_id}"

            # Verify user is a participant in this conversation
            is_participant = await self._check_participant()
            if not is_participant:
                await self.close()
                return

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

        async def disconnect(self, close_code):
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        async def receive(self, text_data):
            try:
                data = json.loads(text_data)
                message_text = data.get('message', '').strip()
                receiver_id = data.get('receiver_id')
            except (json.JSONDecodeError, KeyError):
                return

            if not message_text or not receiver_id:
                return

            # Save to DB
            message = await self._save_message(receiver_id, message_text)
            if not message:
                return

            # Broadcast to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type':       'chat_message',
                    'message_id': message['id'],
                    'text':       message['text'],
                    'sender_id':  message['sender_id'],
                    'sender_un':  message['sender_username'],
                    'timestamp':  message['timestamp'],
                },
            )

        async def chat_message(self, event):
            """Relay group message to this WebSocket client."""
            await self.send(text_data=json.dumps({
                'type':       'message',
                'message_id': event['message_id'],
                'text':       event['text'],
                'sender_id':  event['sender_id'],
                'sender_un':  event['sender_un'],
                'timestamp':  event['timestamp'],
            }))

        # ── Database helpers ──────────────────────────────────────────

        @database_sync_to_async
        def _check_participant(self) -> bool:
            from core.models import Conversation
            try:
                conv = Conversation.objects.get(pk=self.conversation_id)
                return conv.participants.filter(pk=self.user.pk).exists()
            except Conversation.DoesNotExist:
                return False

        @database_sync_to_async
        def _save_message(self, receiver_id: int, text: str) -> dict | None:
            from django.contrib.auth.models import User
            from core.models import Conversation, Message

            try:
                receiver = User.objects.get(pk=receiver_id)
                conv = Conversation.objects.get(pk=self.conversation_id)
                msg = Message.objects.create(
                    conversation=conv,
                    sender=self.user,
                    receiver=receiver,
                    text=text[:2000],
                )
                Conversation.objects.filter(pk=conv.pk).update(updated_at=msg.created_at)
                return {
                    'id':              msg.id,
                    'text':            msg.text,
                    'sender_id':       self.user.id,
                    'sender_username': self.user.username,
                    'timestamp':       msg.created_at.strftime('%H:%M'),
                }
            except Exception as exc:
                logger.error("ChatConsumer._save_message failed: %s", exc)
                return None

else:

    class ChatConsumer:
        """Stub when channels is not installed."""
        pass
