import pandas as pd
import pytest

from utils import check_script, clean_suggestion, get_column_info, parse_answer, run_script, suggest_mapping
from utils.code_executor import ScriptRejected
from utils.llm_script import LLMError


def test_column_info_skips_nulls_and_duplicate_columns():
    df = pd.DataFrame({"a": [1, None, 3], "b": [1, None, 3], "c": ["x", "y", "z"]})
    info = get_column_info(df)
    assert [c["column_name"] for c in info] == ["a", "c"]
    assert info[0]["sample_values"] == [1.0, 3.0]


def test_parse_answer_strips_fences_and_splits_once():
    parsed = parse_answer("Mapped Columns:\na -> b\nCode:\n```python\nprint('Code: here')\n```")
    assert parsed == {"suggestion": "Mapped Columns:\na -> b", "code": "print('Code: here')"}


@pytest.mark.parametrize("answer", ["no section", "Suggestions:\nCode:\n```\n```"])
def test_parse_answer_rejects_unusable_answers(answer):
    with pytest.raises(LLMError):
        parse_answer(answer)


def test_clean_suggestion_drops_rationale():
    assert clean_suggestion("1. a -> b\nRationale:\nbecause") == "1. a -> b\n"
    assert clean_suggestion("1. a -> b") == "1. a -> b"


def test_demo_matcher_honours_explicit_user_mapping():
    info_in = [{"column_name": "Name", "sample_values": []}, {"column_name": "Nickname", "sample_values": []}]
    info_tpl = [{"column_name": "EmployeeName", "sample_values": []}]
    result = suggest_mapping(info_in, info_tpl, "1. Nickname -> EmployeeName")
    assert "1. Nickname -> EmployeeName" in result["suggestion"]
    assert "input_df['Nickname']" in result["code"]


def test_demo_matcher_leaves_unmatched_columns_empty():
    result = suggest_mapping(
        [{"column_name": "zzz", "sample_values": []}], [{"column_name": "Premium", "sample_values": []}]
    )
    assert "(no confident match) -> Premium" in result["suggestion"]
    assert "mapped_df['Premium'] = None" in result["code"]


@pytest.mark.parametrize(
    "code",
    [
        "import subprocess",
        "from os import system",
        "import numpy.lib",
        "open('/etc/passwd')",
        "eval('1')",
        "__import__('os')",
        "input_df.__class__",
        "pd.read_csv('/etc/passwd')",
        "input_df.to_csv('out.csv')",
        "input_df.to_pickle('x')",
        "np.load('x.npy')",
        "input_df.query('a > 1')",
        "getattr(pd, 'read_csv')",
        "global x",
    ],
)
def test_check_script_rejects_unsafe_code(code):
    with pytest.raises(ScriptRejected):
        check_script(code)


def test_check_script_allows_normal_pandas_work():
    check_script(
        "import pandas as pd\nfrom datetime import datetime\n"
        "def map_columns(input_df):\n"
        "    out = pd.DataFrame()\n"
        "    out['d'] = pd.to_datetime(input_df['a']).dt.strftime('%Y')\n"
        "    return out.to_dict()\n"
    )


def test_check_script_reports_syntax_error_line():
    with pytest.raises(ScriptRejected) as caught:
        check_script("x = 1\ndef broken(:\n")
    assert caught.value.line == 2


def test_run_script_times_out():
    result = run_script("while True:\n    pass\n", "a\n1\n", timeout_seconds=2)
    assert "longer than 2 s" in result.error


def test_run_script_has_no_api_key_in_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    result = run_script("import re\nmapped_df = pd.DataFrame({'n': [len(str(datetime))]})", "a\n1\n", 5)
    assert result.records is not None


def test_run_script_ignores_print_output():
    result = run_script("print('debug')\nmapped_df = input_df", "a\n1\n", 5)
    assert result.records == [{"a": 1}]
