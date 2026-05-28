"""Constantes da integração KOReader (HA-specific). Protocol logic lives in pykoreader."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "koreader"

# Sem um check-in dentro desta janela, o dispositivo é considerado offline.
# E-ink dorme com a WiFi desligada, então a janela é generosa.
CONNECTIVITY_TIMEOUT = timedelta(minutes=15)


def signal_update(entry_id: str) -> str:
    """Sinal disparado quando chega telemetria nova para uma entry."""
    return f"{DOMAIN}_update_{entry_id}"


# Serviços
SERVICE_SHOW_MESSAGE = "show_message"
ATTR_MESSAGE = "message"
ATTR_TIMEOUT = "timeout"
SERVICE_GO_TO_PAGE = "go_to_page"
ATTR_PAGE = "page"
SERVICE_GO_TO_PERCENTAGE = "go_to_percentage"
ATTR_PERCENT = "percent"

# Eventos disparados no barramento do HA em transições de telemetria.
EVENT_KOREADER = f"{DOMAIN}_event"
ATTR_EVENT_TYPE = "type"
ATTR_DEVICE_ID = "device_id"
EVENT_SESSION_STARTED = "session_started"
EVENT_SESSION_ENDED = "session_ended"
EVENT_BOOK_FINISHED = "book_finished"
EVENT_BOOK_CHANGED = "book_changed"
EVENT_HIGHLIGHT_ADDED = "highlight_added"

EVENT_TYPES = (
    EVENT_SESSION_STARTED,
    EVENT_SESSION_ENDED,
    EVENT_BOOK_FINISHED,
    EVENT_BOOK_CHANGED,
    EVENT_HIGHLIGHT_ADDED,
)
