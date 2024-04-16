import io
from contextlib import asynccontextmanager
from typing import Annotated

import pandas as pd
import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from utils import (
    ColumnMapper,
    LLMError,
    OpenAIClient,
    clean_suggestion,
    code_runner,
    get_column_info,
    init_db,
    settings,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CSV Column Mapper", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_suggester() -> ColumnMapper:
    if not settings.openai_api_key:
        raise HTTPException(503, "OPENAI_API_KEY is not set")
    return ColumnMapper(OpenAIClient(settings.openai_api_key, settings.openai_model), settings.store_prompts)


def _read_csv(upload: UploadFile) -> pd.DataFrame:
    if not (upload.filename or "").endswith(".csv"):
        raise HTTPException(400, "Invalid file Type. Only .csv files are allowed.")
    return pd.read_csv(io.StringIO(upload.file.read().decode("utf-8")))


@app.get("/")
def home():
    return {"Message": "Backend is running"}


@app.post("/suggest_column_mapping/")
def column_suggestions(
    input_table: Annotated[UploadFile, File()],
    template_table: Annotated[UploadFile, File()],
    suggester: Annotated[ColumnMapper, Depends(get_suggester)],
    suggestion: Annotated[str | None, Form()] = None,
):
    """Suggest how the input CSV's columns map onto the template CSV, plus a
    pandas script that performs the mapping. A `suggestion` (the user's edited
    mapping) asks for a revision that follows it."""
    df_input = _read_csv(input_table)
    df_template = _read_csv(template_table)
    revision = clean_suggestion(suggestion).strip() if suggestion else None
    try:
        return suggester.suggest(get_column_info(df_input), get_column_info(df_template), revision or None)
    except LLMError as exc:
        raise HTTPException(502, str(exc)) from None


@app.post("/column_mapper/")
def column_mapper(code: Annotated[str, Form()], input_table: Annotated[UploadFile, File()]):
    """Run the (possibly edited) mapping script on the input CSV and return the rows."""
    response = code_runner(code, _read_csv(input_table))
    if isinstance(response, pd.DataFrame):
        response = response.to_dict(orient="records")
    return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
