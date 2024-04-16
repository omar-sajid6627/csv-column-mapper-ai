"""Run a user-edited mapping script against an uploaded CSV.

The script comes from the model and the user can edit it, so it is untrusted.
Two layers keep it contained, neither of which is a full sandbox:

1. `check_script` rejects imports outside pandas/numpy/datetime/math/re, dunder
   access, dynamic-code builtins and pandas/numpy file I/O before anything runs.
2. `run_script` executes it in a fresh interpreter with an empty environment
   (no API key), a CPU timeout, a memory cap and a zero file-size limit.
"""

import ast
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass

WORKER = os.path.join(os.path.dirname(__file__), "script_worker.py")
SCRIPT_NAME = "<mapping script>"
ALLOWED_MODULES = {"pandas", "numpy", "datetime", "math", "re"}
BLOCKED_NAMES = set(
    "eval exec compile open input breakpoint help globals locals vars dir getattr setattr "
    "delattr memoryview exit quit".split()
)
BLOCKED_ATTRS = set(
    "eval query system popen load loads save savez savez_compressed savetxt loadtxt "
    "genfromtxt fromfile tofile memmap ctypeslib lib io os sys f_globals f_locals gi_frame "
    "cr_frame tb_frame".split()
)
ALLOWED_TO_ATTRS = set(
    "to_datetime to_numeric to_timedelta to_dict to_list to_numpy to_frame to_string "
    "to_period to_timestamp to_pydatetime to_records".split()
)
MEMORY_LIMIT_BYTES = 1024 * 1024 * 1024


class ScriptRejected(ValueError):
    def __init__(self, message: str, line: int | None = None):
        super().__init__(message)
        self.message = message
        self.line = line


@dataclass
class ScriptResult:
    records: list[dict] | None = None
    error: str | None = None
    line: int | None = None


def check_script(code: str) -> None:
    try:
        tree = ast.parse(code, filename=SCRIPT_NAME)
    except SyntaxError as exc:
        raise ScriptRejected(f"SyntaxError: {exc.msg}", exc.lineno) from None

    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_MODULES or "." in alias.name:
                    raise ScriptRejected(f"import of '{alias.name}' is not allowed", line)
        elif isinstance(node, ast.ImportFrom):
            if node.level or node.module not in ALLOWED_MODULES:
                raise ScriptRejected(f"import from '{node.module}' is not allowed", line)
            for alias in node.names:
                if alias.name.startswith("_") or alias.name in BLOCKED_ATTRS or alias.name == "*":
                    raise ScriptRejected(f"importing '{alias.name}' is not allowed", line)
        elif isinstance(node, ast.Name) and (node.id in BLOCKED_NAMES or node.id.startswith("__")):
            raise ScriptRejected(f"'{node.id}' is not allowed", line)
        elif isinstance(node, ast.Attribute):
            attr = node.attr
            if attr.startswith("_") or attr in BLOCKED_ATTRS or attr.startswith("read_"):
                raise ScriptRejected(f"'.{attr}' is not allowed", line)
            if attr.startswith("to_") and attr not in ALLOWED_TO_ATTRS:
                raise ScriptRejected(f"'.{attr}' is not allowed (no file output)", line)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            raise ScriptRejected("global/nonlocal statements are not allowed", line)


def _limit_child() -> None:  # pragma: no cover - runs in the child process
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))


def run_script(code: str, csv_text: str, timeout_seconds: int) -> ScriptResult:
    """Check, then execute `code` with `input_df` bound to the parsed CSV."""
    check_script(code)
    payload = json.dumps({"code": code, "csv": csv_text})
    env = {"PATH": "/usr/bin:/bin", "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}
    with tempfile.TemporaryDirectory() as workdir:
        try:
            done = subprocess.run(
                [sys.executable, "-I", WORKER],
                input=payload,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=workdir,
                env=env,
                preexec_fn=_limit_child if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired:
            return ScriptResult(error=f"Script took longer than {timeout_seconds} s and was stopped")

    try:
        reply = json.loads(done.stdout)
    except json.JSONDecodeError:
        return ScriptResult(error="Script crashed before producing a result (memory limit or file write?)")
    if reply.get("ok"):
        return ScriptResult(records=reply["records"])
    return ScriptResult(error=reply.get("error", "Script failed"), line=reply.get("line"))
