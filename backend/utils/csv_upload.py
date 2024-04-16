"""Turn an uploaded CSV into a DataFrame, enforcing type and size limits."""

import io

import pandas as pd
from fastapi import UploadFile

# Browsers disagree on the type of a .csv file (Windows often reports the Excel type).
ACCEPTED_CONTENT_TYPES = {
    "",
    "text/csv",
    "application/csv",
    "text/plain",
    "application/vnd.ms-excel",
    "application/octet-stream",
}


class UploadError(ValueError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def read_csv_upload(upload: UploadFile, max_bytes: int, max_columns: int) -> tuple[pd.DataFrame, str]:
    """Return the parsed frame and the decoded text (the script runner re-parses the text)."""
    name = upload.filename or "upload"
    if not name.lower().endswith(".csv"):
        raise UploadError(415, f"{name}: only .csv files are accepted")
    content_type = (upload.content_type or "").split(";")[0].strip().lower()
    if content_type not in ACCEPTED_CONTENT_TYPES:
        raise UploadError(415, f"{name}: unexpected content type {content_type}")

    raw = upload.file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise UploadError(413, f"{name}: file is larger than {max_bytes // 1024} KB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise UploadError(400, f"{name}: file is not UTF-8 text") from None

    try:
        frame = pd.read_csv(io.StringIO(text))
    except pd.errors.EmptyDataError:
        raise UploadError(400, f"{name}: file is empty") from None
    except pd.errors.ParserError as exc:
        raise UploadError(400, f"{name}: could not parse CSV ({exc})") from None

    if frame.columns.empty:
        raise UploadError(400, f"{name}: no columns found")
    if len(frame.columns) > max_columns:
        raise UploadError(413, f"{name}: more than {max_columns} columns")
    return frame, text
