"""
core/services/message_service.py
---------------------------------
Business logic for direct messaging.
"""

from django.contrib.auth.models import User

from core.models import Conversation, Message
from core.utils.constants import MESSAGE_MAX_LENGTH


def get_or_create_conversation(user_a: User, user_b: User) -> tuple:
    """Return (conversation, created) for the two users."""
    return Conversation.get_or_create_for(user_a, user_b)


def get_inbox(user: User):
    """Return the user's conversations sorted by most recent."""
    return (
        user.conversations
        .prefetch_related('participants', 'participants__profile', 'messages')
        .order_by('-updated_at')
    )


def get_conversation_messages(conversation: Conversation, user: User):
    """
    Return all messages in a conversation and mark unread ones as read.
    """
    # Mark as read
    conversation.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    return (
        conversation.messages
        .select_related('sender', 'sender__profile')
        .order_by('created_at')
    )


def send_message(sender: User, receiver: User, text: str) -> Message:
    """
    Create and send a message between two users.
    Creates the conversation if it doesn't exist.
    Truncates message to MESSAGE_MAX_LENGTH.
    """
    text = text.strip()[:MESSAGE_MAX_LENGTH]
    if not text:
        raise ValueError("Message text cannot be empty.")

    conv, _ = get_or_create_conversation(sender, receiver)
    message = Message.objects.create(
        conversation=conv,
        sender=sender,
        receiver=receiver,
        text=text,
    )
    # Update conversation timestamp
    Conversation.objects.filter(pk=conv.pk).update(updated_at=message.created_at)
    return message
