"""Testa coalescing e teto da fila de comandos."""

from custom_components.koreader.const import queue_command


class _Runtime:
    def __init__(self):
        self.commands = []


def test_idempotent_commands_coalesce():
    rt = _Runtime()
    queue_command(rt, {"type": "set_frontlight", "value": 10})
    queue_command(rt, {"type": "set_frontlight", "value": 25})
    assert rt.commands == [{"type": "set_frontlight", "value": 25}]


def test_messages_accumulate():
    rt = _Runtime()
    queue_command(rt, {"type": "show_message", "text": "a"})
    queue_command(rt, {"type": "show_message", "text": "b"})
    assert len(rt.commands) == 2


def test_queue_is_capped():
    rt = _Runtime()
    for i in range(30):
        queue_command(rt, {"type": "show_message", "text": str(i)})
    assert len(rt.commands) == 20
    assert rt.commands[-1] == {"type": "show_message", "text": "29"}


def test_page_turn_does_not_coalesce():
    rt = _Runtime()
    queue_command(rt, {"type": "page_turn", "value": 1})
    queue_command(rt, {"type": "page_turn", "value": 1})
    assert len(rt.commands) == 2


def test_set_warmth_coalesces():
    rt = _Runtime()
    queue_command(rt, {"type": "set_warmth", "value": 10})
    queue_command(rt, {"type": "set_warmth", "value": 40})
    assert rt.commands == [{"type": "set_warmth", "value": 40}]
