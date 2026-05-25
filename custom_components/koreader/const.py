"""Constantes da integração KOReader."""

from __future__ import annotations

DOMAIN = "koreader"

# Nome do sinal de dispatcher por config entry (atualização de telemetria).
def signal_update(entry_id: str) -> str:
    """Sinal disparado quando chega telemetria nova para uma entry."""
    return f"{DOMAIN}_update_{entry_id}"

# Tipos de comando enfileirados para o Kindle (devolvidos na resposta do webhook).
CMD_SET_FRONTLIGHT = "set_frontlight"
CMD_SHOW_MESSAGE = "show_message"
CMD_SET_WIFI = "set_wifi"
CMD_SYNC_NOW = "sync_now"

# Serviço
SERVICE_SHOW_MESSAGE = "show_message"
ATTR_MESSAGE = "message"
ATTR_TIMEOUT = "timeout"
