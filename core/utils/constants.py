"""
core/utils/constants.py
-----------------------
Project-wide constants.  Import from here instead of scattering magic
numbers / strings throughout the codebase.
"""

# ── File size limits (bytes) ──────────────────────────────────────────
PROFILE_IMAGE_MAX_MB  = 5
STORY_IMAGE_MAX_MB    = 10
POST_IMAGE_MAX_MB     = 15

PROFILE_IMAGE_MAX_BYTES = PROFILE_IMAGE_MAX_MB * 1024 * 1024
STORY_IMAGE_MAX_BYTES   = STORY_IMAGE_MAX_MB   * 1024 * 1024
POST_IMAGE_MAX_BYTES    = POST_IMAGE_MAX_MB    * 1024 * 1024

# ── Allowed MIME types ────────────────────────────────────────────────
ALLOWED_IMAGE_TYPES = [
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
]

# ── Upload paths ──────────────────────────────────────────────────────
UPLOAD_PATH_PROFILES = 'profiles/'
UPLOAD_PATH_POSTS    = 'posts/'
UPLOAD_PATH_STORIES  = 'stories/'
UPLOAD_PATH_MESSAGES = 'messages/'

# ── Pagination ────────────────────────────────────────────────────────
FEED_PAGE_SIZE     = 5
EXPLORE_PAGE_SIZE  = 24
SAVED_PAGE_SIZE    = 12
NOTIF_PAGE_SIZE    = 20
SEARCH_RESULT_SIZE = 10

# ── Story expiry ──────────────────────────────────────────────────────
STORY_EXPIRY_HOURS = 24

# ── Comment / message limits ──────────────────────────────────────────
COMMENT_MAX_LENGTH  = 2200
MESSAGE_MAX_LENGTH  = 2000
CAPTION_MAX_LENGTH  = 2200
BIO_MAX_LENGTH      = 150

# ── Anti-spam ─────────────────────────────────────────────────────────
COMMENT_SPAM_WINDOW_SECONDS = 10

# ── Notification types ────────────────────────────────────────────────
NOTIF_LIKE           = 'like'
NOTIF_COMMENT        = 'comment'
NOTIF_FOLLOW         = 'follow'
NOTIF_FOLLOW_REQUEST = 'follow_request'
NOTIF_STORY_REPLY    = 'story_reply'
NOTIF_STORY_REACTION = 'story_reaction'

# ── WebSocket group name prefixes ─────────────────────────────────────
WS_CHAT_GROUP_PREFIX  = 'chat_'
WS_NOTIF_GROUP_PREFIX = 'notif_user_'
WS_PRESENCE_GROUP     = 'presence'

# ── Session / cache keys ──────────────────────────────────────────────
CACHE_LAST_SEEN_KEY = 'last_seen_{user_id}'
