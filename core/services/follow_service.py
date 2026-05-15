"""
follow_service.py
-----------------
Encapsulates follow / unfollow / follow-request logic so that
view functions stay thin and this behaviour can be reused or tested
independently.
"""

from core.models import Follow, FollowRequest, Notification


def get_following_ids(user):
    """Return a flat list of user IDs that *user* is following."""
    return list(
        Follow.objects.filter(follower=user).values_list('following_id', flat=True)
    )


def get_sent_request_ids(user):
    """Return a flat list of user IDs that *user* has a pending follow request to."""
    return list(
        FollowRequest.objects.filter(sender=user).values_list('receiver_id', flat=True)
    )


def follow_user(requester, target):
    """
    Follow *target* from *requester*.

    - If target has a private account: create a FollowRequest + notification.
    - If target is public: create a Follow + notification directly.
    - Silently does nothing if already following.

    Returns: 'already_following' | 'requested' | 'followed'
    """
    if Follow.objects.filter(follower=requester, following=target).exists():
        return 'already_following'

    profile = getattr(target, 'profile', None)
    is_private = profile.private_account if profile else False

    if is_private:
        _, created = FollowRequest.objects.get_or_create(
            sender=requester,
            receiver=target,
        )
        if created:
            Notification.objects.get_or_create(
                sender=requester,
                receiver=target,
                notif_type='follow_request',
                defaults={'is_read': False},
            )
        return 'requested'
    else:
        Follow.objects.get_or_create(follower=requester, following=target)
        Notification.objects.get_or_create(
            sender=requester,
            receiver=target,
            notif_type='follow',
            defaults={'is_read': False},
        )
        return 'followed'


def unfollow_user(requester, target):
    """Remove a follow relationship or pending request from requester → target."""
    Follow.objects.filter(follower=requester, following=target).delete()
    
    # Also cancel any pending follow request and its notification
    FollowRequest.objects.filter(sender=requester, receiver=target).delete()
    Notification.objects.filter(sender=requester, receiver=target, notif_type='follow_request').delete()


def accept_follow_request(follow_request):
    """
    Accept a pending FollowRequest:
    - Creates the Follow record
    - Sends a 'follow' notification to the original requester
    - Deletes the pending follow_request notification
    - Deletes the FollowRequest itself
    """
    Follow.objects.get_or_create(
        follower=follow_request.sender,
        following=follow_request.receiver,
    )
    Notification.objects.get_or_create(
        sender=follow_request.receiver,
        receiver=follow_request.sender,
        notif_type='follow',
    )
    Notification.objects.filter(
        sender=follow_request.sender,
        receiver=follow_request.receiver,
        notif_type='follow_request',
    ).delete()
    follow_request.delete()


def decline_follow_request(follow_request):
    """
    Decline a pending FollowRequest:
    - Deletes the related follow_request notification
    - Deletes the FollowRequest itself
    """
    Notification.objects.filter(
        sender=follow_request.sender,
        receiver=follow_request.receiver,
        notif_type='follow_request',
    ).delete()
    follow_request.delete()
