"""
message_views.py
----------------
Handles all messaging / conversation views:
  - messages_view      – Renders the messaging UI
  - get_conversations  – Returns JSON list of conversations
  - get_messages       – Returns JSON messages with a specific user
  - send_message       – Saves a new message to a Conversation
"""

import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from core.models import Conversation, Message


# ─────────────────────────────────────────────
#  INBOX
# ─────────────────────────────────────────────

@login_required
def messages_view(request):
    """Render the messaging UI with Conversation-based inbox."""
    me = request.user
    conversations = (
        me.conversations
        .prefetch_related('participants', 'participants__profile', 'messages')
        .order_by('-updated_at')
    )
    return render(request, 'message.html', {
        'conversations': conversations,
        'me': me,
    })


# ─────────────────────────────────────────────
#  CONVERSATIONS LIST  (AJAX)
# ─────────────────────────────────────────────

@login_required
def get_conversations(request):
    """Return JSON list of conversations (one per partner, with latest message)."""
    me = request.user
    conversations = (
        me.conversations
        .prefetch_related('participants', 'participants__profile', 'messages')
        .order_by('-updated_at')
    )

    result = []
    for conv in conversations:
        partner = next(
            (p for p in conv.participants.all() if p.id != me.id),
            None,
        )
        if not partner:
            continue

        latest = conv.messages.last()
        unread = conv.messages.filter(receiver=me, is_read=False).exists()

        result.append({
            'username':   partner.username,
            'full_name':  partner.get_full_name() or partner.username,
            'avatar_url': (
                partner.profile.profile_image.url
                if hasattr(partner, 'profile') and partner.profile.profile_image else None
            ),
            'preview': (
                ('You: ' if latest and latest.sender_id == me.id else '')
                + (latest.text[:60] if latest else '')
            ),
            'time':   latest.created_at.strftime('%H:%M') if latest else '',
            'unread': unread,
        })

    return JsonResponse({'conversations': result})


# ─────────────────────────────────────────────
#  MESSAGES WITH A USER  (AJAX)
# ─────────────────────────────────────────────

@login_required
def get_messages(request, username):
    """Return JSON messages between me and <username>. Marks them as read."""
    me    = request.user
    other = get_object_or_404(User, username=username)

    conv, _ = Conversation.get_or_create_for(me, other)

    msgs = conv.messages.select_related('sender').order_by('created_at')

    # Mark incoming messages as read
    msgs.filter(receiver=me, is_read=False).update(is_read=True)

    data = [{
        'id':      m.id,
        'text':    m.text,
        'out':     m.sender_id == me.id,
        'time':    m.created_at.strftime('%H:%M'),
        'sender':  m.sender.username,
        'is_read': m.is_read,
    } for m in msgs]

    other_info = {
        'username':   other.username,
        'full_name':  other.get_full_name() or other.username,
        'avatar_url': (
            other.profile.profile_image.url
            if hasattr(other, 'profile') and other.profile.profile_image else None
        ),
    }

    return JsonResponse({'messages': data, 'other': other_info})


# ─────────────────────────────────────────────
#  SEND MESSAGE  (AJAX POST)
# ─────────────────────────────────────────────

@login_required
@require_POST
def send_message(request, username):
    """POST — save a new message, linked to the Conversation for this pair."""
    me    = request.user
    other = get_object_or_404(User, username=username)

    try:
        body = json.loads(request.body)
        text = body.get('text', '').strip()
    except Exception:
        text = request.POST.get('text', '').strip()

    if not text:
        return JsonResponse({'error': 'Empty message'}, status=400)

    if len(text) > 1000:
        return JsonResponse({'error': 'Message too long (max 1000 chars).'}, status=400)

    conv, _ = Conversation.get_or_create_for(me, other)

    msg = Message.objects.create(
        conversation=conv,
        sender=me,
        receiver=other,
        text=text,
    )

    # Bump conversation updated_at so inbox re-sorts correctly
    conv.save(update_fields=['updated_at'])

    return JsonResponse({
        'id':      msg.id,
        'text':    msg.text,
        'out':     True,
        'time':    msg.created_at.strftime('%H:%M'),
        'is_read': False,
    })
