import pytest

from emporio_agent.config import PROJECT_ROOT
from emporio_agent.data.loader import load_store


@pytest.fixture(scope="session")
def store():
    return load_store(PROJECT_ROOT / "data" / "raw")
