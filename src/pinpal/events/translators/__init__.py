"""Source-specific translators that convert raw payloads into canonical events."""

from pinpal.events.translators.instagram import translate_instagram_follows
from pinpal.events.translators.manual import translate_manual_observation
from pinpal.events.translators.whatsapp import translate_whatsapp_group

__all__ = [
    "translate_instagram_follows",
    "translate_manual_observation",
    "translate_whatsapp_group",
]
