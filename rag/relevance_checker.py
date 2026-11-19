import re

from rag.constants import QUESTION_TYPE_SUMMARY


STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for",
    "is", "are", "was", "were", "be", "been", "being", "this", "that",
    "these", "those", "it", "its", "how", "what", "why", "when",
    "where", "who", "which", "does", "do", "did", "can", "could",
    "would", "should", "about", "with", "from", "as", "at", "by",
    "into", "over", "after", "before", "between", "your", "my",
}


def extract_question_terms(question):
    tokens = re.findall(r"[a-z0-9]+", question.lower())
    return [
        token
        for token in tokens
        if token not in STOPWORDS and len(token) > 2
    ]


def term_overlap_count(question, text):
    terms = extract_question_terms(question)
    if not terms:
        return 0, 0.0

    lowered = text.lower()
    hits = sum(1 for term in terms if term in lowered)
    return hits, hits / len(terms)


def is_chunk_relevant(question, text, score, threshold):
    """Decide if one chunk is usable evidence for a specific question.

    Strong semantic matches (comfortably above the calibrated threshold)
    are accepted even with weak lexical overlap. Borderline matches must
    also share at least one content term with the question.
    """

    if score is None or score < threshold:
        return False

    hits, ratio = term_overlap_count(question, text)

    if score >= threshold + 0.08:
        return True

    return hits >= 1 or ratio >= 0.2


def validate_relevance(
    question,
    question_type,
    retrieval_results,
    threshold,
):
    """Server-side relevance gate used before LLM generation."""

    if question_type == QUESTION_TYPE_SUMMARY:
        accepted = [
            result
            for result in retrieval_results
            if result.get("document") is not None
        ]

        if not accepted:
            return {
                "is_relevant": False,
                "accepted": [],
                "reason": "No representative document chunks were retrieved.",
            }

        return {
            "is_relevant": True,
            "accepted": accepted,
            "reason": "Document-level representative chunks were retrieved.",
        }

    accepted = []

    for result in retrieval_results:
        document = result.get("document")
        text = document.page_content if document is not None else ""

        if is_chunk_relevant(
            question=question,
            text=text,
            score=result.get("score"),
            threshold=threshold,
        ):
            accepted.append(result)

    if not accepted:
        return {
            "is_relevant": False,
            "accepted": [],
            "reason": (
                "Retrieved chunks did not pass calibrated relevance "
                "validation."
            ),
        }

    return {
        "is_relevant": True,
        "accepted": accepted,
        "reason": "Sufficient on-document evidence was retrieved.",
    }
