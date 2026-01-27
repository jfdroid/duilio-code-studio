"""
Pytest Configuration
====================
Shared fixtures and configuration for all tests.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from typing import Generator

# Common fixtures
@pytest.fixture
def test_workspace_path() -> str:
    """Return a test workspace path."""
    return str(Path.home() / "Desen")

@pytest.fixture
def test_model() -> str:
    """Return default test model."""
    return "qwen2.5-coder:14b"
