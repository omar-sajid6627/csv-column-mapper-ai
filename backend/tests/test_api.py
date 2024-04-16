from conftest import INPUT_CSV, TEMPLATE_CSV, FakeClient, csv_file

import main
from utils import ColumnMapper, LLMError
from utils.database import SessionLocal
from utils.models import LlmData

ANSWER = (
    "Suggestions:\n1. Name -> EmployeeName\nRationale:\n1. Same person\n"
    "Code:\n```python\ndef map_columns(input_df):\n"
    "    return input_df.rename(columns={'Name': 'EmployeeName'})[['EmployeeName']]\n\n"
    "mapped_df = map_columns(input_df)\n```\n"
)


def _files():
    return {
        "input_table": csv_file("input.csv", INPUT_CSV),
        "template_table": csv_file("template.csv", TEMPLATE_CSV),
    }


def test_health_reports_demo_mode(client):
    assert client.get("/").json() == {"Message": "Backend is running"}
    assert client.get("/health").json() == {"status": "ok", "llm_mode": "demo"}


def test_suggest_in_demo_mode_maps_every_template_column(client):
    body = client.post("/suggest_column_mapping/", files=_files()).json()
    for pair in (
        "PolicyDate -> Date",
        "Name -> EmployeeName",
        "PlanType -> Plan",
        "Policy_ID -> PolicyNumber",
        "PremiumAmount -> Premium",
    ):
        assert pair in body["suggestion"]
    assert "mapped_df = map_columns(input_df)" in body["code"]


def test_demo_code_runs_through_column_mapper(client):
    code = client.post("/suggest_column_mapping/", files=_files()).json()["code"]
    rows = client.post(
        "/column_mapper/", data={"code": code}, files={"input_table": csv_file("input.csv", INPUT_CSV)}
    ).json()
    assert rows[0] == {
        "Date": "2024-01-03",
        "EmployeeName": "Ada Example",
        "Plan": "Gold",
        "PolicyNumber": "PX-0001",
        "Premium": 150,
    }
    assert len(rows) == 3


def test_suggest_with_fake_llm_parses_answer_and_stores_prompt(client):
    fake = FakeClient(ANSWER)
    main.app.dependency_overrides[main.get_suggester] = lambda: ColumnMapper(fake, store_prompts=True)
    with SessionLocal() as db:
        before = db.query(LlmData).count()

    body = client.post("/suggest_column_mapping/", files=_files()).json()

    assert body["suggestion"].startswith("Suggestions:")
    assert "```" not in body["code"]
    assert body["code"].endswith("mapped_df = map_columns(input_df)")
    assert "PolicyDate" in fake.prompts[0] and "EmployeeName" in fake.prompts[0]
    with SessionLocal() as db:
        assert db.query(LlmData).count() == before + 1


def test_revision_uses_edited_suggestion_without_rationale(client):
    fake = FakeClient(ANSWER)
    main.app.dependency_overrides[main.get_suggester] = lambda: ColumnMapper(fake, store_prompts=False)
    edited = "Mapped Columns:\n1. Name -> EmployeeName\nRationale:\n1. should not be sent"
    client.post("/suggest_column_mapping/", files=_files(), data={"suggestion": edited})
    assert "1. Name -> EmployeeName" in fake.prompts[0]
    assert "should not be sent" not in fake.prompts[0]


def test_answer_without_code_section_is_a_502(client):
    main.app.dependency_overrides[main.get_suggester] = lambda: ColumnMapper(FakeClient("no code here"), False)
    response = client.post("/suggest_column_mapping/", files=_files())
    assert response.status_code == 502
    assert "Code:" in response.json()["detail"]


def test_llm_failure_is_a_502(client):
    class Down:
        def complete(self, prompt):
            raise LLMError("OpenAI request failed: APIConnectionError")

    main.app.dependency_overrides[main.get_suggester] = lambda: ColumnMapper(Down(), False)
    assert client.post("/suggest_column_mapping/", files=_files()).status_code == 502


def test_openai_mode_without_key_is_a_503(client, monkeypatch):
    monkeypatch.setattr(main.settings.__class__, "effective_llm_mode", property(lambda self: "openai"))
    response = client.post("/suggest_column_mapping/", files=_files())
    assert response.status_code == 503


def test_small_csv_is_accepted(client):
    # Fewer rows than the sample size used to make every column vanish from the prompt.
    files = {"input_table": csv_file("a.csv", "Name\nAda\n"), "template_table": csv_file("b.csv", "EmployeeName\nJo\n")}
    assert "Name -> EmployeeName" in client.post("/suggest_column_mapping/", files=files).json()["suggestion"]


def test_rejects_non_csv_extension(client):
    files = _files() | {"input_table": csv_file("input.txt", INPUT_CSV)}
    response = client.post("/suggest_column_mapping/", files=files)
    assert response.status_code == 415
    assert "input.txt" in response.json()["detail"]


def test_rejects_unexpected_content_type(client):
    files = _files() | {"template_table": csv_file("template.csv", TEMPLATE_CSV, "image/png")}
    assert client.post("/suggest_column_mapping/", files=files).status_code == 415


def test_rejects_oversized_upload(client):
    big = "a,b\n" + "1,2\n" * 2000
    files = _files() | {"input_table": csv_file("input.csv", big)}
    response = client.post("/suggest_column_mapping/", files=files)
    assert response.status_code == 413


def test_rejects_too_many_columns(client):
    wide = ",".join(f"c{i}" for i in range(25)) + "\n" + ",".join("1" * 25) + "\n"
    files = _files() | {"input_table": csv_file("input.csv", wide)}
    assert client.post("/suggest_column_mapping/", files=files).status_code == 413


def test_rejects_empty_and_non_utf8_files(client):
    empty = _files() | {"input_table": csv_file("input.csv", "")}
    assert client.post("/suggest_column_mapping/", files=empty).json()["detail"] == "input.csv: file is empty"
    latin = {"input_table": ("input.csv", "Name\nJos\xe9\n".encode("latin-1"), "text/csv")}
    response = client.post("/column_mapper/", data={"code": "mapped_df = input_df"}, files=latin)
    assert response.status_code == 400


def test_accepts_utf8_bom(client):
    files = {"input_table": csv_file("input.csv", "﻿Name\nAda\n")}
    rows = client.post("/column_mapper/", data={"code": "mapped_df = input_df"}, files=files).json()
    assert rows == [{"Name": "Ada"}]


def test_column_mapper_reports_runtime_error_with_line(client):
    code = "x = 1\nmapped_df = input_df['Missing']\n"
    response = client.post(
        "/column_mapper/", data={"code": code}, files={"input_table": csv_file("input.csv", INPUT_CSV)}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "KeyError: 'Missing'", "line": 2}


def test_column_mapper_rejects_unsafe_script_before_running(client):
    response = client.post(
        "/column_mapper/",
        data={"code": "import os\nmapped_df = input_df"},
        files={"input_table": csv_file("input.csv", INPUT_CSV)},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "import of 'os' is not allowed"


def test_column_mapper_requires_a_dataframe(client):
    response = client.post(
        "/column_mapper/", data={"code": "mapped_df = 3"}, files={"input_table": csv_file("input.csv", INPUT_CSV)}
    )
    assert response.status_code == 422
    assert "DataFrame" in response.json()["detail"]


def test_column_mapper_keeps_backslash_n_in_string_literals(client):
    code = "mapped_df = pd.DataFrame({'joined': ['a\\\\nb']})"
    rows = client.post(
        "/column_mapper/", data={"code": code}, files={"input_table": csv_file("input.csv", INPUT_CSV)}
    ).json()
    assert rows == [{"joined": "a\\nb"}]
