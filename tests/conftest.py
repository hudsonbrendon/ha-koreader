"""Fixtures de teste."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Habilita o carregamento de custom_components nos testes."""
    yield
