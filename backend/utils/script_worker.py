"""Child-process entry point for code_executor.run_script. Reads JSON on stdin,
writes JSON on stdout. Kept free of project imports so it starts with `-I`."""

import builtins
import contextlib
import datetime
import io
import json
import math
import re
import sys
import traceback

import numpy as np
import pandas as pd

SCRIPT_NAME = "<mapping script>"
MODULES = {"pandas": pd, "numpy": np, "datetime": datetime, "math": math, "re": re}
SAFE_BUILTINS = (
    "abs all any bool dict enumerate filter float format frozenset int isinstance len list "
    "map max min print range reversed round set sorted str sum tuple zip Exception "
    "ValueError KeyError TypeError IndexError"
).split()


def _import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name not in MODULES:
        raise ImportError(f"import of '{name}' is not allowed")
    return MODULES[name]


def _error_line(exc: BaseException) -> int | None:
    for frame in reversed(traceback.extract_tb(exc.__traceback__)):
        if frame.filename == SCRIPT_NAME:
            return frame.lineno
    return None


def main() -> None:
    request = json.load(sys.stdin)
    input_df = pd.read_csv(io.StringIO(request["csv"]))
    safe_builtins = {name: getattr(builtins, name) for name in SAFE_BUILTINS}
    safe_builtins["__import__"] = _import
    namespace = {
        "__builtins__": safe_builtins,
        "__name__": "mapping_script",
        "input_df": input_df,
        "pd": pd,
        "np": np,
        "datetime": datetime,
        "mapped_df": None,
    }
    try:
        # print() output would corrupt the JSON reply on stdout, so it is discarded.
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(request["code"], SCRIPT_NAME, "exec"), namespace)
    except Exception as exc:
        json.dump({"ok": False, "error": f"{type(exc).__name__}: {exc}", "line": _error_line(exc)}, sys.stdout)
        return

    mapped = namespace.get("mapped_df")
    if not isinstance(mapped, pd.DataFrame):
        json.dump({"ok": False, "error": "The script must assign a DataFrame to mapped_df"}, sys.stdout)
        return
    records = json.loads(mapped.to_json(orient="records", date_format="iso"))
    json.dump({"ok": True, "records": records}, sys.stdout)


if __name__ == "__main__":
    main()
