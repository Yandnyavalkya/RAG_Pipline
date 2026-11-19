"""Shared Phase 1 RAG intelligence constants."""

QUESTION_TYPE_SUMMARY = "document_summary"
QUESTION_TYPE_SPECIFIC = "specific"

REFUSAL_MESSAGE = (
    "I couldn't find sufficient information about this question "
    "in the uploaded document. Please ask something related to "
    "the document."
)

# Representative probes for document-level questions.
# These are not a lowered copy of SIMILARITY_THRESHOLD.
SUMMARY_PROBES = (
    "abstract introduction overview main topic",
    "conclusion summary contributions findings",
    "this paper presents we propose the document describes",
)
