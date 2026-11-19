from rag.constants import QUESTION_TYPE_SUMMARY


def _clip(value, lower=0.0, upper=1.0):
    return max(lower, min(upper, value))


def _mean(values):
    if not values:
        return 0.0

    return sum(values) / len(values)


def calibrate_similarity(mean_score, threshold):
    """Map cosine similarity into a calibrated 0-1 evidence signal.

    Raw cosine similarity is not returned as a percentage probability.
    Scores near the rejection threshold map low; scores typical of
    labelled relevant Transformer chunks (about 0.55-0.70) map high.
    """

    upper = max(threshold + 0.30, 0.70)
    span = upper - threshold

    if span <= 0:
        return 0.0

    return _clip((mean_score - threshold) / span)


def assess_confidence(
    question_type,
    accepted_results,
    citation_report,
    grounding,
    refused,
    threshold,
):
    if refused or not accepted_results:
        return {
            "level": "none",
            "score": 0.0,
            "signals": {
                "retrieval_relevance": 0.0,
                "evidence_coverage": 0.0,
                "citation_support": 0.0,
                "answer_grounding": 0.0,
            },
        }

    scores = [
        result["score"]
        for result in accepted_results
        if result.get("score") is not None
    ]
    mean_score = _mean(scores)

    if question_type == QUESTION_TYPE_SUMMARY:
        retrieval_relevance = _clip(0.55 + (0.05 * min(len(accepted_results), 6)))
    else:
        retrieval_relevance = calibrate_similarity(mean_score, threshold)

    evidence_coverage = _clip(len(accepted_results) / 4)
    citation_support = _clip(citation_report.get("citation_coverage", 0.0))
    answer_grounding = _clip(grounding)

    composite = (
        (0.35 * retrieval_relevance)
        + (0.20 * evidence_coverage)
        + (0.20 * citation_support)
        + (0.25 * answer_grounding)
    )
    composite = round(_clip(composite), 2)

    if composite >= 0.75:
        level = "high"
    elif composite >= 0.55:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "score": composite,
        "signals": {
            "retrieval_relevance": round(retrieval_relevance, 2),
            "evidence_coverage": round(evidence_coverage, 2),
            "citation_support": round(citation_support, 2),
            "answer_grounding": round(answer_grounding, 2),
        },
    }
