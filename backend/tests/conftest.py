"""
Pytest configuration for the backend tests.

Forces a single asyncio event loop for the whole test session so that the
module-level `AsyncIOMotorClient` keeps working across async tests/fixtures.
"""
import asyncio
import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Override pytest-asyncio's default function-scoped loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
