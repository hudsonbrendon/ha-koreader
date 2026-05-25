"""Fixtures de teste."""

import threading

import pytest

import pytest_homeassistant_custom_component.plugins as ha_plugins

# Nome da thread daemon efêmera que o loop.shutdown_default_executor() do harness
# cria em Python 3.12 (build do Homebrew) e que, neste ambiente, demora a encerrar.
# Não é um defeito da integração: todos os asserts dos testes passam; apenas o
# check estrito de threads do verify_cleanup (pytest-homeassistant-custom-component)
# falha na teardown por causa dessa corrida. Os interpretadores 3.13/3.14 do
# Homebrew estão quebrados (pyexpat), então 3.12.4 é o único utilizável.
_BENIGN_THREAD_MARKER = "_run_safe_shutdown_loop"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Habilita o carregamento de custom_components nos testes."""
    yield


@pytest.fixture(autouse=True)
def _tolerate_executor_shutdown_thread(monkeypatch):
    """Ignora a thread daemon benigna de shutdown do executor no check de threads.

    Envolve threading.enumerate (usado por verify_cleanup) para omitir a thread
    `_run_safe_shutdown_loop`, evitando um falso-positivo na teardown do harness
    sem mascarar nenhuma asserção dos próprios testes.
    """
    real_enumerate = threading.enumerate

    def _filtered_enumerate():
        return [t for t in real_enumerate() if _BENIGN_THREAD_MARKER not in t.name]

    monkeypatch.setattr(ha_plugins.threading, "enumerate", _filtered_enumerate)
    yield
