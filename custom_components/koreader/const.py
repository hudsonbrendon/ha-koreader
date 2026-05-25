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
CMD_SET_WARMTH = "set_warmth"
CMD_SET_FRONTLIGHT_POWER = "set_frontlight_power"
CMD_PAGE_TURN = "page_turn"
CMD_GOTO_PAGE = "goto_page"
CMD_REFRESH = "refresh"

# Serviço
SERVICE_SHOW_MESSAGE = "show_message"
ATTR_MESSAGE = "message"
ATTR_TIMEOUT = "timeout"
SERVICE_GO_TO_PAGE = "go_to_page"
ATTR_PAGE = "page"

# Tipos cujo último valor manda (idempotentes): substituem o anterior do mesmo tipo.
# NÃO inclui page_turn: cada virada de página é um evento discreto.
COALESCE_TYPES = {
    CMD_SET_FRONTLIGHT, CMD_SET_WIFI, CMD_SYNC_NOW,
    CMD_SET_WARMTH, CMD_SET_FRONTLIGHT_POWER, CMD_REFRESH, CMD_GOTO_PAGE,
}
# Teto da fila para não crescer sem limite enquanto o Kindle está offline.
MAX_QUEUED_COMMANDS = 20


def queue_command(runtime, command: dict) -> None:
    """Enfileira um comando para o próximo check-in do Kindle.

    Para comandos idempotentes (frontlight/wifi/sync) substitui o anterior do
    mesmo tipo (last-write-wins) em vez de acumular. Aplica um teto na fila.
    """
    if command["type"] in COALESCE_TYPES:
        runtime.commands = [
            c for c in runtime.commands if c.get("type") != command["type"]
        ]
    runtime.commands.append(command)
    if len(runtime.commands) > MAX_QUEUED_COMMANDS:
        runtime.commands = runtime.commands[-MAX_QUEUED_COMMANDS:]
