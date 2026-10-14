import pytest


@pytest.fixture(autouse=True)
def _no_event_network(monkeypatch):
    """Tests must never reach the network for event data (NSE ban list, yfinance earnings dates)."""
    monkeypatch.setenv('EDGE_EVENTS', '0')
