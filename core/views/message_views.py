"""
message_views.py
----------------
Handles all messaging / conversation views:
  - messages_view      – Renders the messaging UI
  - get_conversations  – Returns JSON list of conversations
  - get_messages       – Returns JSON messages with a specific user (paginated)
  - send_message       – Saves a new message to a Conversation
  - edit_message       – Edit own message
  - delete_message     – Soft-delete (unsend) own message
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods

from core.models import Conversation, Message

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _serialize_message(m, me_id):
    """Serialize a single Message for the API response."""
    reply_data = None
    try:
        if m.reply_to_id and not m.reply_to.is_deleted:
            rt = m.reply_to
            reply_data = {
                'id':   rt.id,
                'text': rt.text,
                'out':  rt.sender_id == me_id,
            }
    except Exception:
        pass

    return {
        'id':         m.id,
        'text':       m.text if not m.is_deleted else None,
        'out':        m.sender_id == me_id,
        'time':       m.created_at.strftime('%H:%M'),
        'sender':     m.sender.username,
        'is_read':    m.is_read,
        'is_edited':  m.is_edited,
        'is_deleted': m.is_deleted,
        'reply_to':   reply_data,
    }


# ─────────────────────────────────────────────
#  INBOX
# ─────────────────────────────────────────────

@login_required
def messages_view(request):
    """Render the messaging UI with Conversation-based inbox."""
    me = request.user
    # We don't prefetch messages here to avoid memory issues
    conversations = (
        me.conversations
        .prefetch_related('participants', 'participants__profile')
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
        .prefetch_related('participants', 'participants__profile')
        .order_by('-updated_at')
    )

    result = []
    for conv in conversations:
        try:
            partner = next(
                (p for p in conv.participants.all() if p.id != me.id),
                None,
            )
            if not partner:
                continue

            # Get latest non-deleted message without loading all messages
            latest = conv.messages.filter(is_deleted=False).only('text', 'sender_id', 'created_at').last()
            unread = conv.messages.filter(receiver=me, is_read=False, is_deleted=False).exists()

            result.append({
                'username':   partner.username,
                'full_name':  partner.get_full_name() or partner.username,
                'avatar_url': (
                    partner.profile.profile_image.url
                    if hasattr(partner, 'profile') and partner.profile.profile_image else None
                ),
                'preview': (
                    (('You: ' if latest.sender_id == me.id else '') + latest.text[:60])
                    if latest else ''
                ),
                'time':   latest.created_at.strftime('%H:%M') if latest else '',
                'unread': unread,
            })
        except Exception as e:
            logger.error(f"Error processing conversation {conv.id}: {e}")
            continue

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

    PAGE = 40
    qs = conv.messages.select_related('sender', 'reply_to', 'reply_to__sender')

    before_id = request.GET.get('before')
    if before_id:
        try:
            qs = qs.filter(id__lt=int(before_id))
        except (ValueError, TypeError):
            pass
    
    msgs = list(qs.order_by('-created_at')[:PAGE])
    msgs.reverse()

    # Mark incoming messages as read
    conv.messages.filter(receiver=me, is_read=False).update(is_read=True)

    data = [_serialize_message(m, me.id) for m in msgs]

    other_info = {
        'username':   other.username,
        'full_name':  other.get_full_name() or other.username,
        'avatar_url': (
            other.profile.profile_image.url
            if hasattr(other, 'profile') and other.profile.profile_image else None
        ),
    }

    # Simplified has_more check
    has_more = len(data) == PAGE

    return JsonResponse({'messages': data, 'other': other_info, 'has_more': has_more})


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
        body    = json.loads(request.body)
        text    = body.get('text', '').strip()
        reply_id = body.get('reply_to')
    except Exception:
        text     = request.POST.get('text', '').strip()
        reply_id = None

    if not text:
        return JsonResponse({'error': 'Empty message'}, status=400)

    conv, _ = Conversation.get_or_create_for(me, other)

    reply_obj = None
    if reply_id:
        try:
            reply_obj = Message.objects.get(id=int(reply_id), conversation=conv)
        except (Message.DoesNotExist, ValueError):
            pass

    msg = Message.objects.create(
        conversation=conv,
        sender=me,
        receiver=other,
        text=text[:2000],
        reply_to=reply_obj,
    )

    conv.save(update_fields=['updated_at'])

    return JsonResponse(_serialize_message(msg, me.id))


# ─────────────────────────────────────────────
#  EDIT MESSAGE  (AJAX PATCH)
# ─────────────────────────────────────────────

@login_required
@require_http_methods(['PATCH', 'POST'])
def edit_message(request, message_id):
    """PATCH /messages/<id>/edit/ — edit own message text."""
    me  = request.user
    msg = get_object_or_404(Message, id=message_id, sender=me)

    if msg.is_deleted:
        return JsonResponse({'error': 'Cannot edit deleted'}, status=400)

    try:
        body = json.loads(request.body)
        new_text = body.get('text', '').strip()
    except Exception:
        new_text = request.POST.get('text', '').strip()

    if not new_text:
        return JsonResponse({'error': 'Empty'}, status=400)

    msg.text = new_text
    msg.is_edited = True
    msg.save(update_fields=['text', 'is_edited', 'updated_at'])

    return JsonResponse({'ok': True, 'text': msg.text})


# ─────────────────────────────────────────────
#  UNSEND / DELETE MESSAGE  (AJAX DELETE/POST)
# ─────────────────────────────────────────────

@login_required
@require_http_methods(['DELETE', 'POST'])
def delete_message(request, message_id):
    """DELETE /messages/<id>/delete/ — soft-delete own message."""
    me  = request.user
    msg = get_object_or_404(Message, id=message_id, sender=me)

    msg.is_deleted = True
    msg.save(update_fields=['is_deleted', 'updated_at'])

    return JsonResponse({'ok': True})
