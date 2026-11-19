import re

from rag.document_metadata import document_name_from_source
from rag.relevance_checker import extract_question_terms


CITATION_PATTERN = re.compile(r"\[Source\s+(\d+)\]", re.IGNORECASE)


def excerpt_text(text, max_length=280):
    cleaned = re.sub(r"\s+", " ", text or "").strip()

    if len(cleaned) <= max_length:
        return cleaned

    return cleaned[: max_length - 3].rstrip() + "..."


def build_sources(filtered_results):
    sources = []

    for index, result in enumerate(filtered_results, start=1):
        document = result["document"]
        metadata = document.metadata
        source_path = metadata.get("source", "Unknown source")
        page = metadata.get(
            "page_label",
            metadata.get("page", "Unknown"),
        )

        try:
            page_number = int(page)
        except (TypeError, ValueError):
            page_number = page

        sources.append({
            "source_id": index,
            "chunk_id": result.get("id") or metadata.get("chunk_id"),
            "document": metadata.get("document_name")
            or document_name_from_source(source_path),
            "document_id": metadata.get("document_id"),
            "page": page_number,
            "path": source_path,
            "excerpt": excerpt_text(document.page_content),
            "start_index": metadata.get("start_index"),
            "score": result.get("score"),
            "cited": False,
        })

    return sources


def extract_cited_source_ids(answer):
    return {
        int(match)
        for match in CITATION_PATTERN.findall(answer or "")
    }


def mark_cited_sources(sources, answer):
    cited_ids = extract_cited_source_ids(answer)
    valid_ids = {source["source_id"] for source in sources}

    for source in sources:
        source["cited"] = source["source_id"] in cited_ids

    invalid_citations = sorted(cited_ids - valid_ids)

    return {
        "cited_ids": sorted(cited_ids & valid_ids),
        "invalid_citations": invalid_citations,
        "citation_coverage": (
            len(cited_ids & valid_ids) / len(sources)
            if sources else 0.0
        ),
    }


def grounding_score(answer, context, refusal_message):
    """Estimate how much of the answer is supported by retrieved text.

    This is a lexical support heuristic, not a probability and not a
    cosine similarity score.
    """

    if not answer or answer.strip() == refusal_message:
        return 0.0

    if not context:
        return 0.0

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", answer)
        if sentence.strip()
        and not CITATION_PATTERN.fullmatch(sentence.strip())
    ]

    if not sentences:
        return 0.0

    context_lower = context.lower()
    supported = 0

    for sentence in sentences:
        terms = extract_question_terms(sentence)
        if not terms:
            continue

        hits = sum(1 for term in terms if term in context_lower)
        if hits / len(terms) >= 0.35 or hits >= 3:
            supported += 1

    return supported / len(sentences)
