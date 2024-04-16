import os
import sys
import tempfile

_DB_DIR = tempfile.mkdtemp(prefix="csvmap-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_DIR}/test.db"
os.environ["OPENAI_API_KEY"] = ""
os.environ["LLM_MODE"] = "demo"
os.environ["MAX_UPLOAD_BYTES"] = "4096"
os.environ["MAX_COLUMNS"] = "20"
os.environ["SCRIPT_TIMEOUT_SECONDS"] = "5"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

# Synthetic data only: invented names and policy numbers.
INPUT_CSV = (
    "PolicyDate,Name,PlanType,Policy_ID,PremiumAmount\n"
    "2024-01-03,Ada Example,Gold,PX-0001,150\n"
    "2024-01-04,Ben Sample,Silver,PX-0002,100\n"
    "2024-01-05,Cy Placeholder,Bronze,PX-0003,50\n"
)
TEMPLATE_CSV = "Date,EmployeeName,Plan,PolicyNumber,Premium\n2023-05-01,Jo Demo,Gold,AB12345,150\n"


class FakeClient:
    """Stands in for OpenAI: records prompts and replays a canned answer."""

    def __init__(self, answer: str):
        self.answer = answer
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answer


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


def csv_file(name: str, text: str, content_type: str = "text/csv"):
    return (name, text.encode(), content_type)
