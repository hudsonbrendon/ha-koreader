"""Smoke test do toolchain."""

from custom_components.koreader.const import DOMAIN


def test_domain():
    assert DOMAIN == "koreader"
