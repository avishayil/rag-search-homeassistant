"""Unit tests for the pure history-formatting/parsing helpers."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from custom_components.rag_search.search import _format_history, _parse_iso


def _state(entity_id: str, state: str) -> SimpleNamespace:
    """Build a minimal fake state object."""
    return SimpleNamespace(
        entity_id=entity_id,
        state=state,
        last_changed=datetime(2024, 10, 1, 12, 0, tzinfo=timezone.utc),
    )


def test_parse_iso_handles_trailing_z():
    """A trailing Z is accepted and parsed as UTC."""
    parsed = _parse_iso("2024-10-01T00:00:00Z")
    assert parsed == datetime(2024, 10, 1, 0, 0, tzinfo=timezone.utc)


def test_parse_iso_invalid_raises():
    """An invalid timestamp raises ValueError for the caller to handle."""
    with pytest.raises(ValueError):
        _parse_iso("not-a-date")


def test_format_history_returns_lines():
    """Each state becomes a readable line."""
    history_data = {
        "sensor.temperature": [
            _state("sensor.temperature", "20"),
            _state("sensor.temperature", "21"),
        ]
    }
    lines = _format_history("sensor.temperature", history_data, num_items=50)
    assert len(lines) == 2
    assert lines[0].startswith("sensor.temperature changed to 20 at")


def test_format_history_respects_num_items():
    """Only the most recent num_items entries are kept."""
    states = [_state("sensor.temperature", str(i)) for i in range(10)]
    lines = _format_history(
        "sensor.temperature", {"sensor.temperature": states}, num_items=3
    )
    assert len(lines) == 3
    assert "changed to 9 at" in lines[-1]


def test_format_history_missing_entity_returns_empty():
    """An entity with no history yields no lines."""
    assert _format_history("sensor.unknown", {}, num_items=50) == []
