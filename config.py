import os

OFFLINE = os.getenv("OFFLINE", "false").lower() in ("1","true","yes")
DANBOORU_BASE = "https://danbooru.donmai.us"
USER_AGENT = os.getenv("USER_AGENT", "sd-prompt-app/1.0")
TAGS_LIMIT_PER_BUCKET = int(os.getenv("TAGS_LIMIT_PER_BUCKET", "50"))
DISPLAY_CAP_PER_BUCKET = int(os.getenv("DISPLAY_CAP_PER_BUCKET", "10"))  # nb maximum renvoyé par /tags
