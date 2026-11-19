from rag.constants import (
    QUESTION_TYPE_SPECIFIC,
    QUESTION_TYPE_SUMMARY,
    REFUSAL_MESSAGE,
)
from rag.question_classifier import classify_question
from rag.relevance_checker import validate_relevance
from rag.confidence import assess_confidence
from rag.source_validator import (
    build_sources,
    mark_cited_sources,
    grounding_score,
)
from rag.retrieval import build_metadata_filter, diversify_by_page

from langchain_core.documents import Document


def make_result(vector_id, score, text, page=1, source="manual.pdf"):
    document = Document(
        page_content=text,
        metadata={
            "source": source,
            "page": page,
            "document_name": source,
            "document_id": "doc_123",
            "chunk_id": vector_id,
            "start_index": 0,
        },
    )
    return {
        "id": vector_id,
        "score": score,
        "document": document,
    }


def test_question_classifier():
    summary_questions = [
        "What is the document about?",
        "What is this paper about?",
        "Summarize this document",
        "Give me an overview",
        "What is the main topic of the document?",
    ]

    specific_questions = [
        "What is attention?",
        "How can I block my debit card?",
        "How does photosynthesis work?",
        "Why is positional encoding necessary?",
    ]

    for question in summary_questions:
        assert classify_question(question) == QUESTION_TYPE_SUMMARY, question

    for question in specific_questions:
        assert classify_question(question) == QUESTION_TYPE_SPECIFIC, question


def test_specific_relevance_keeps_calibrated_threshold():
    results = [
        make_result(
            "chunk_attention",
            0.62,
            "Multi-head attention allows the model to attend jointly.",
        ),
        make_result(
            "chunk_weak",
            0.22,
            "Photosynthesis converts light energy into chemical energy.",
        ),
    ]

    decision = validate_relevance(
        question="What is attention?",
        question_type=QUESTION_TYPE_SPECIFIC,
        retrieval_results=results,
        threshold=0.40,
    )

    assert decision["is_relevant"] is True
    assert len(decision["accepted"]) == 1
    assert decision["accepted"][0]["id"] == "chunk_attention"


def test_unrelated_question_is_rejected():
    results = [
        make_result(
            "chunk_transformer",
            0.31,
            "The Transformer uses stacked self-attention layers.",
        ),
        make_result(
            "chunk_encoder",
            0.28,
            "The encoder is composed of a stack of identical layers.",
        ),
    ]

    decision = validate_relevance(
        question="How does photosynthesis work?",
        question_type=QUESTION_TYPE_SPECIFIC,
        retrieval_results=results,
        threshold=0.40,
    )

    assert decision["is_relevant"] is False
    assert decision["accepted"] == []


def test_borderline_match_requires_term_overlap():
    results = [
        make_result(
            "chunk_unrelated",
            0.41,
            "Account holders may update a registered mobile number.",
        )
    ]

    decision = validate_relevance(
        question="How does photosynthesis work in plants?",
        question_type=QUESTION_TYPE_SPECIFIC,
        retrieval_results=results,
        threshold=0.40,
    )

    assert decision["is_relevant"] is False


def test_summary_does_not_use_query_threshold():
    results = [
        make_result(
            "intro",
            0.33,
            "This paper introduces the Transformer architecture.",
            page=1,
        ),
        make_result(
            "method",
            0.29,
            "The encoder and decoder use multi-head attention.",
            page=3,
        ),
    ]

    decision = validate_relevance(
        question="What is the document about?",
        question_type=QUESTION_TYPE_SUMMARY,
        retrieval_results=results,
        threshold=0.40,
    )

    assert decision["is_relevant"] is True
    assert len(decision["accepted"]) == 2


def test_confidence_is_not_raw_cosine():
    accepted = [
        make_result("c1", 0.62, "Self-attention computes representations."),
        make_result("c2", 0.58, "Multi-head attention uses several subspaces."),
        make_result("c3", 0.55, "The encoder contains six identical layers."),
    ]

    confidence = assess_confidence(
        question_type=QUESTION_TYPE_SPECIFIC,
        accepted_results=accepted,
        citation_report={"citation_coverage": 0.67},
        grounding=0.8,
        refused=False,
        threshold=0.40,
    )

    assert confidence["score"] != round(0.62, 2)
    assert 0.0 <= confidence["score"] <= 1.0
    assert confidence["level"] in {"high", "medium", "low"}

    refused = assess_confidence(
        question_type=QUESTION_TYPE_SPECIFIC,
        accepted_results=[],
        citation_report={},
        grounding=0.0,
        refused=True,
        threshold=0.40,
    )

    assert refused["level"] == "none"
    assert refused["score"] == 0.0


def test_source_attribution_and_grounding():
    results = [
        make_result(
            "chunk_101",
            0.61,
            "Card blocking procedure is available in internet banking.",
            page=12,
            source="Bank_User_Manual.pdf",
        )
    ]

    sources = build_sources(results)
    answer = (
        "You can block a debit card through internet banking "
        "[Source 1]."
    )
    citation_report = mark_cited_sources(sources, answer)
    context = "Card blocking procedure is available in internet banking."

    assert sources[0]["document"] == "Bank_User_Manual.pdf"
    assert sources[0]["page"] == 12
    assert sources[0]["chunk_id"] == "chunk_101"
    assert sources[0]["excerpt"]
    assert sources[0]["cited"] is True
    assert citation_report["cited_ids"] == [1]
    assert grounding_score(answer, context, REFUSAL_MESSAGE) > 0


def test_metadata_filter_and_page_diversity():
    assert build_metadata_filter(None) is None
    assert build_metadata_filter(["doc_123"]) == {
        "document_id": {"$eq": "doc_123"}
    }
    assert build_metadata_filter(["doc_1", "doc_2"]) == {
        "document_id": {"$in": ["doc_1", "doc_2"]}
    }

    results = [
        make_result("a", 0.9, "page 1", page=1),
        make_result("b", 0.8, "page 1 again", page=1),
        make_result("c", 0.7, "page 4", page=4),
        make_result("d", 0.6, "page 2", page=2),
    ]

    diversified = diversify_by_page(results, top_k=3)
    pages = [
        item["document"].metadata["page"]
        for item in diversified
    ]

    assert pages == [1, 2, 4]


def main():
    test_question_classifier()
    test_specific_relevance_keeps_calibrated_threshold()
    test_unrelated_question_is_rejected()
    test_borderline_match_requires_term_overlap()
    test_summary_does_not_use_query_threshold()
    test_confidence_is_not_raw_cosine()
    test_source_attribution_and_grounding()
    test_metadata_filter_and_page_diversity()
    print("INTELLIGENCE UNIT TESTS PASSED")


if __name__ == "__main__":
    main()
