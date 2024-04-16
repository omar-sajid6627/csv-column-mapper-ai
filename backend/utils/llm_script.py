"""Column-mapping suggestions: the prompt, the model call and the answer parsing."""

import re
from typing import Protocol

import pandas as pd

from .models import create_llm_data
from .templates import main_template, revision_template

SAMPLE_SIZE = 5
_FENCE = re.compile(r"^```[a-zA-Z]*\s*$", re.MULTILINE)


class LLMError(RuntimeError):
    """The model could not be reached or answered in an unusable shape."""


class CompletionClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class OpenAIClient:
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, prompt: str) -> str:
        from openai import OpenAIError

        try:
            reply = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1500,
            )
        except OpenAIError as exc:
            raise LLMError(f"OpenAI request failed: {exc.__class__.__name__}") from exc
        content = reply.choices[0].message.content if reply.choices else None
        if not content:
            raise LLMError("OpenAI returned an empty answer")
        return content


def get_column_info(df: pd.DataFrame) -> list[dict]:
    """Name, dtype and a few non-null sample values per column; columns that
    duplicate an earlier column's values are left out to keep the prompt short."""
    df = df.loc[:, ~df.T.duplicated(keep="first")]
    return [
        {
            "column_name": str(col),
            "data_type": str(df[col].dtype),
            "sample_values": df[col].dropna().head(SAMPLE_SIZE).tolist(),
        }
        for col in df.columns
    ]


def parse_answer(answer: str) -> dict:
    """Split the model's answer at "Code:" into suggestion text and a script."""
    code_at = answer.find("Code:")
    if code_at == -1:
        raise LLMError("The model's answer has no 'Code:' section")
    suggestion = answer[:code_at].strip()
    code = _FENCE.sub("", answer[code_at + len("Code:") :]).strip()
    if not code:
        raise LLMError("The model's answer has an empty 'Code:' section")
    return {"suggestion": suggestion, "code": code}


class ColumnMapper:
    """Builds the prompt, asks the model and stores the exchange."""

    def __init__(self, client: CompletionClient, store_prompts: bool = True):
        self.client = client
        self.store_prompts = store_prompts

    def suggest(self, info_input: list[dict], info_template: list[dict], suggestion: str | None = None) -> dict:
        if suggestion:
            prompt = revision_template.format(info_input=info_input, info_template=info_template, suggestion=suggestion)
        else:
            prompt = main_template.format(info_input=info_input, info_template=info_template)
        answer = self.client.complete(prompt)
        if self.store_prompts:
            create_llm_data(prompt=prompt, response=answer)
        return parse_answer(answer)
