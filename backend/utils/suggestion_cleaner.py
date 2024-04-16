def clean_suggestion(suggestion: str) -> str:
    """Keep the mapping list and drop the "Rationale:" part the model added."""
    rationale_at = suggestion.find("Rationale:")
    return suggestion if rationale_at == -1 else suggestion[:rationale_at]
