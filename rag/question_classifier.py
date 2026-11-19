import re

from rag.constants import (
    QUESTION_TYPE_SPECIFIC,
    QUESTION_TYPE_SUMMARY,
)


SUMMARY_PATTERNS = (
    r"\bwhat is (this|the|that) (document|paper|pdf|file|manual|report|article) about\b",
    r"\bwhat (is|are) (this|the|these) (document|paper|pdf|file|manual|report|article)s? (about|on)\b",
    r"\bwhat does (this|the|that) (document|paper|pdf|file|manual|report) (talk about|discuss|cover|describe|say)\b",
    r"\b(summarize|summarise|summary of) (this|the|that)? ?(document|paper|pdf|file|manual|report|article)?\b",
    r"\bgive (me )?(an |a )?(overview|summary|synopsis)\b",
    r"\b(main topic|main idea|key takeaways?|tl;?dr)\b",
    r"\bwhat is the (main )?(topic|subject|purpose) of (this|the) (document|paper|pdf|file|manual)\b",
    r"\bdescribe (this|the) (document|paper|pdf|file|manual)\b",
)


def classify_question(question):
    """Classify a user question as document summary or specific.

    Unrelated questions are not classified here. They are rejected later
    by retrieval relevance validation.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    normalized = re.sub(r"\s+", " ", question.strip().lower())
    normalized = re.sub(r"[?!.,]+$", "", normalized)

    for pattern in SUMMARY_PATTERNS:
        if re.search(pattern, normalized):
            return QUESTION_TYPE_SUMMARY

    return QUESTION_TYPE_SPECIFIC
