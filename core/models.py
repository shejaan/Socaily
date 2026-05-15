from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


# ─────────────────────────────────────────────
#  PROFILE
# ─────────────────────────────────────────────

class Profile(models.Model):
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio             = models.TextField(blank=True)
    website         = models.URLField(blank=True)
    profile_image   = models.ImageField(upload_to='profiles/', blank=True, null=True)
    private_account = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name        = 'Profile'
        verbose_name_plural = 'Profiles'


# ─────────────────────────────────────────────
#  POST
# ─────────────────────────────────────────────

class Post(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    image      = models.ImageField(upload_to='posts/')
    caption    = models.TextField(blank=True)
    location   = models.CharField(max_length=255, blank=True)
    saved_by   = models.ManyToManyField(User, related_name='saved_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} – {self.id}"

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count()

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Posts'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            # Standalone index for explore/trending queries that order by created_at globally
            models.Index(fields=['-created_at'], name='post_created_at_idx'),
        ]


# ─────────────────────────────────────────────
#  FOLLOW
# ─────────────────────────────────────────────

class Follow(models.Model):
    follower   = models.ForeignKey(User, related_name='following_set', on_delete=models.CASCADE)
    following  = models.ForeignKey(User, related_name='follower_set',  on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.follower} follows {self.following}"

    class Meta:
        verbose_name_plural = 'Follows'
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follow'),
        ]
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['following']),
        ]


# ─────────────────────────────────────────────
#  FOLLOW REQUEST
# ─────────────────────────────────────────────

class FollowRequest(models.Model):
    sender    = models.ForeignKey(User, related_name='sent_requests',     on_delete=models.CASCADE)
    receiver  = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver}"

    class Meta:
        verbose_name_plural = 'Follow Requests'
        constraints = [
            models.UniqueConstraint(fields=['sender', 'receiver'], name='unique_follow_request'),
        ]
        indexes = [
            models.Index(fields=['receiver']),
            models.Index(fields=['sender'], name='followreq_sender_named_idx'),
        ]


# ─────────────────────────────────────────────
#  LIKE
# ─────────────────────────────────────────────

class Like(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post       = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} liked post {self.post_id}"

    class Meta:
        verbose_name_plural = 'Likes'
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_like'),
        ]
        indexes = [
            # Compound index covers both the uniqueness check and per-post like counts
            models.Index(fields=['post', 'user'], name='like_post_user_idx'),
            models.Index(fields=['user'], name='like_user_idx'),
        ]


# ─────────────────────────────────────────────
#  COMMENT
# ─────────────────────────────────────────────

class Comment(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    text       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} on post {self.post_id}"

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Comments'
        indexes = [
            models.Index(fields=['post', 'created_at'], name='comment_post_time_idx'),
        ]


# ─────────────────────────────────────────────
#  NOTIFICATION
# ─────────────────────────────────────────────

class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ('like',           'Like'),
        ('comment',        'Comment'),
        ('follow',         'Follow'),
        ('follow_request', 'Follow Request'),
    )

    sender     = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE)
    receiver   = models.ForeignKey(User, related_name='notifications',      on_delete=models.CASCADE)
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.notif_type})"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['receiver', 'is_read']),
            models.Index(fields=['receiver', '-created_at']),
        ]


# ─────────────────────────────────────────────
#  CONVERSATION  (groups messages between two users)
# ─────────────────────────────────────────────

class Conversation(models.Model):
    """
    Represents a unique channel between exactly two users.
    Messages belong to a Conversation, not directly to sender/receiver.
    Easily extendable to group chats later.
    """
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def __str__(self):
        names = ', '.join(u.username for u in self.participants.all())
        return f"Conversation({names})"

    @classmethod
    def get_or_create_for(cls, user_a, user_b):
        """
        Return the existing Conversation between user_a and user_b,
        or create a new one.  Always returns (conversation, created).
        """
        # Find conversations where BOTH users are participants
        conv = (
            cls.objects
            .filter(participants=user_a)
            .filter(participants=user_b)
            .first()
        )
        if conv:
            return conv, False
        conv = cls.objects.create()
        conv.participants.set([user_a, user_b])
        return conv, True

    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'Conversations'
        indexes = [
            # Speeds up inbox sort (ordering = ['-updated_at'])
            models.Index(fields=['-updated_at'], name='conversation_updated_idx'),
        ]


# ─────────────────────────────────────────────
#  MESSAGE
# ─────────────────────────────────────────────

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE,
        related_name='messages',
    )
    sender   = models.ForeignKey(User, related_name='sent_messages',     on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    text     = models.TextField()
    is_read  = models.BooleanField(default=False)
    # Reply threading
    reply_to = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='replies'
    )
    # Edit / soft-delete
    is_edited  = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.text[:30]}"

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['conversation', 'created_at'], name='message_conv_time_idx'),
            models.Index(fields=['sender', 'receiver'],         name='message_sender_receiver_idx'),
        ]


# ─────────────────────────────────────────────
#  STORY
# ─────────────────────────────────────────────

class Story(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    image      = models.ImageField(upload_to='stories/')
    caption    = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} story {self.id}"

    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=24)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'
        indexes = [
            models.Index(fields=['user', '-created_at'], name='story_user_time_idx'),
        ]


class StoryView(models.Model):
    """Tracks which users have seen a story."""
    story   = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer  = models.ForeignKey(User,  on_delete=models.CASCADE, related_name='story_views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['story', 'viewer'], name='unique_story_view'),
        ]
        verbose_name_plural = 'Story Views'


class StoryReaction(models.Model):
    """Emoji reactions to stories."""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_reactions')
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Story Reactions'


class StoryReply(models.Model):
    """Text replies to stories (often creates a DM conversation)."""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Story Replies'


# ─────────────────────────────────────────────
#  HIGHLIGHTS
# ─────────────────────────────────────────────

class Highlight(models.Model):
    """A collection of saved stories displayed on a user profile."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    title = models.CharField(max_length=50)
    cover_image = models.ImageField(upload_to='highlights/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    class Meta:
        ordering = ['-created_at']


class HighlightItem(models.Model):
    """Maps a past Story to a Highlight album."""
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='items')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='highlight_items')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['highlight', 'story'], name='unique_highlight_story'),
        ]


# ─────────────────────────────────────────────
#  CLOSE FRIENDS
# ─────────────────────────────────────────────

class CloseFriend(models.Model):
    """List of close friends for private stories."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='close_friends_list')
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='close_friend_of')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'friend'], name='unique_close_friend'),
        ]

