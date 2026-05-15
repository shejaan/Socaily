from core.models import Notification, FollowRequest

def notifications_context(request):
    """
    Globally injects notifications, follow_requests, and unread count into 
    all templates so the navbar bell works on every page.
    """
    if not request.user.is_authenticated:
        return {}
    
    me = request.user
    
    follow_requests = (
        FollowRequest.objects
        .filter(receiver=me)
        .select_related('sender', 'sender__profile')
    )
    
    notifications = (
        Notification.objects
        .filter(receiver=me)
        .select_related('sender', 'sender__profile', 'post')
        .order_by('-created_at')[:20]
    )
    
    unread_notifications_count = Notification.objects.filter(receiver=me, is_read=False).count()
    
    return {
        'follow_requests': follow_requests,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    }
