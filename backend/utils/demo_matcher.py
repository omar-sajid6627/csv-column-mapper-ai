"""Offline stand-in for the model: matches columns by name similarity.

It lets the app run end to end without an OpenAI key, and returns the same
{"suggestion", "code"} shape so the UI cannot tell the difference.
"""

import re
from difflib import SequenceMatcher

MATCH_THRESHOLD = 0.6
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_EXPLICIT = re.compile(r"^\s*(?:\d+\.\s*)?(.+?)\s*->\s*(.+?)\s*$")


# Abbreviations that name the same thing in column headers.
_SYNONYMS = {"id": "number", "no": "number", "num": "number", "nr": "number", "dob": "birthdate", "amt": "amount"}


def _tokens(name: str) -> set[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    words = re.split(r"[^a-zA-Z0-9]+", spaced.lower())
    return {_SYNONYMS.get(w, w) for w in words if w}


def _similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    if ta == tb:
        return 1.0
    flat_a, flat_b = "".join(sorted(ta)), "".join(sorted(tb))
    containment = 0.85 if ta <= tb or tb <= ta else 0.0
    overlap = len(ta & tb) / len(ta | tb)
    return max(containment, overlap, 0.9 * SequenceMatcher(None, flat_a, flat_b).ratio())


def _best_pairs(input_names: list[str], targets: list[str], fixed: dict[str, str]) -> dict[str, tuple[str, float]]:
    """Greedy one-to-one assignment: the strongest pairs claim their columns first."""
    taken = set(fixed.values())
    scored = sorted(
        ((_similarity(t, c), t, c) for t in targets if t not in fixed for c in input_names if c not in taken),
        reverse=True,
    )
    pairs: dict[str, tuple[str, float]] = {}
    for score, target, source in scored:
        if score < MATCH_THRESHOLD:
            break
        if target not in pairs and source not in taken:
            pairs[target] = (source, score)
            taken.add(source)
    return pairs


def _explicit_pairs(suggestion: str | None, inputs: set[str], targets: set[str]) -> dict[str, str]:
    """Read "source -> target" lines from a suggestion the user edited."""
    pairs: dict[str, str] = {}
    for line in (suggestion or "").splitlines():
        found = _EXPLICIT.match(line)
        if found and found.group(1) in inputs and found.group(2) in targets:
            pairs[found.group(2)] = found.group(1)
    return pairs


def _looks_like_iso_dates(info: dict) -> bool:
    samples = [str(v) for v in info["sample_values"]]
    return bool(samples) and all(_ISO_DATE.match(v) for v in samples)


def suggest_mapping(info_input: list[dict], info_template: list[dict], suggestion: str | None = None) -> dict:
    input_names = [c["column_name"] for c in info_input]
    explicit = _explicit_pairs(suggestion, set(input_names), {c["column_name"] for c in info_template})

    target_names = [c["column_name"] for c in info_template]
    matched = _best_pairs(input_names, target_names, explicit)

    lines, rationale = ["Mapped Columns:"], ["Rationale:"]
    code = ["def map_columns(input_df):", "    mapped_df = pd.DataFrame()"]
    for number, target in enumerate(info_template, start=1):
        name = target["column_name"]
        if name in explicit:
            source, reason = explicit[name], "your edit"
        elif name in matched:
            source, score = matched[name]
            reason = f"name similarity {score:.2f}"
        else:
            source, reason = None, ""

        if source is None:
            lines.append(f"{number}. (no confident match) -> {name}")
            rationale.append(f"{number}. No similar column name")
            code.append(f"    mapped_df[{name!r}] = None")
            continue

        lines.append(f"{number}. {source} -> {name}")
        rationale.append(f"{number}. {reason.capitalize()}")
        if _looks_like_iso_dates(target):
            code.append(
                f"    mapped_df[{name!r}] = "
                f"pd.to_datetime(input_df[{source!r}], errors='coerce').dt.strftime('%Y-%m-%d')"
            )
        else:
            code.append(f"    mapped_df[{name!r}] = input_df[{source!r}]")

    code += ["    return mapped_df", "", "", "mapped_df = map_columns(input_df)"]
    return {"suggestion": "\n".join(lines + [""] + rationale), "code": "\n".join(code)}
