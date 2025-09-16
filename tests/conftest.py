import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so `import app` works when running pytest from repo root
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


