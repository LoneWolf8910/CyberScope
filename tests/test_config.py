"""Tests for configuration defaults."""

import os
import tempfile

from core.statistics import Statistics


def test_statistics_defaults():
    stats = Statistics()
    assert stats.total_packets == 0
    assert stats.total_bytes == 0


def test_temp_file_creation():
    # Sanity check that tmpdir works (environment test).
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test")
        path = f.name
    assert os.path.exists(path)
    os.unlink(path)
