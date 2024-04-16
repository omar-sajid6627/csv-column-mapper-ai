from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from utils import (
    ColumnMapper,
    LLMError,
    OpenAIClient,
    ScriptRejected,
    UploadError,
    clean_suggestion,
    get_column_info,
    init_db,
    read_csv_upload,
    run_script,
    settings,
    suggest_mapping,
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


class DemoSuggester:
    def suggest(self, info_input, info_template, suggestion=None):
        return suggest_mapping(info_input, info_template, suggestion)


def get_suggester():
    """Dependency: the model-backed mapper, or the offline matcher in demo mode."""
    if settings.effective_llm_mode == "openai":
        if not settings.openai_api_key:
            raise HTTPException(503, "LLM_MODE=openai but OPENAI_API_KEY is not set")
        return ColumnMapper(OpenAIClient(settings.openai_api_key, settings.openai_model), settings.store_prompts)
    return DemoSuggester()


def _read(upload: UploadFile):
    try:
        return read_csv_upload(upload, settings.max_upload_bytes, settings.max_columns)
    except UploadError as exc:
        raise HTTPException(exc.status_code, exc.message) from None


@app.get("/")
def home():
    return {"Message": "Backend is running"}


@app.get("/health")
def health():
    return {"status": "ok", "llm_mode": settings.effective_llm_mode}


@app.post("/suggest_column_mapping/")
def column_suggestions(
    input_table: Annotated[UploadFile, File()],
    template_table: Annotated[UploadFile, File()],
    suggester: Annotated[ColumnMapper | DemoSuggester, Depends(get_suggester)],
    suggestion: Annotated[str | None, Form()] = None,
):
    """Suggest how the input CSV's columns map onto the template CSV, plus a
    pandas script that performs the mapping. A `suggestion` (the user's edited
    mapping) asks for a revision that follows it."""
    df_input, _ = _read(input_table)
    df_template, _ = _read(template_table)
    revision = clean_suggestion(suggestion).strip() if suggestion else None
    try:
        return suggester.suggest(get_column_info(df_input), get_column_info(df_template), revision or None)
    except LLMError as exc:
        raise HTTPException(502, str(exc)) from None


@app.post("/column_mapper/")
def column_mapper(code: Annotated[str, Form()], input_table: Annotated[UploadFile, File()]):
    """Run the (possibly edited) mapping script on the input CSV and return the rows."""
    _, csv_text = _read(input_table)
    try:
        result = run_script(code, csv_text, settings.script_timeout_seconds)
    except ScriptRejected as exc:
        return JSONResponse({"detail": exc.message, "line": exc.line}, status_code=422)
    if result.error:
        return JSONResponse({"detail": result.error, "line": result.line}, status_code=422)
    return result.records


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
