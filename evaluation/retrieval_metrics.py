
def precision_at_k(retrieved_keys, relevant_keys, k=4):
    """
    Measures the fraction of the top K retrieved chunks
    that are relevant.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero")

    retrieved = retrieved_keys[:k]

    if not retrieved:
        return 0.0

    relevant = set(relevant_keys)

    hits = sum(
        1 for key in retrieved if key in relevant
    )

    return hits / len(retrieved)


def recall_at_k(retrieved_keys, relevant_keys, k=4):
    """
    Measures the fraction of all relevant chunks
    that appear in the top K results.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero")

    relevant = set(relevant_keys)

    if not relevant:
        return None

    retrieved = retrieved_keys[:k]

    hits = sum(
        1 for key in retrieved if key in relevant
    )

    return hits / len(relevant)


def reciprocal_rank(retrieved_keys, relevant_keys):
    """
    Returns the reciprocal rank of the first relevant result.
    """
    relevant = set(relevant_keys)

    if not relevant:
        return None

    for rank, key in enumerate(retrieved_keys, start=1):
        if key in relevant:
            return 1 / rank

    return 0.0


def mean_reciprocal_rank(results):
    """
    Calculates MRR across multiple questions.

    results format:
    [
        {
            "retrieved_keys": [...],
            "relevant_keys": [...]
        }
    ]
    """
    scores = []

    for result in results:
        score = reciprocal_rank(
            result["retrieved_keys"],
            result["relevant_keys"]
        )

        if score is not None:
            scores.append(score)

    if not scores:
        return None

    return sum(scores) / len(scores)


def evaluate_retrieval(
    retrieved_keys,
    relevant_keys,
    k=4
):
    """
    Calculates all retrieval metrics for one question.
    """
    return {
        "precision_at_k": precision_at_k(
            retrieved_keys, relevant_keys, k
        ),
        "recall_at_k": recall_at_k(
            retrieved_keys, relevant_keys, k
        ),
        "reciprocal_rank": reciprocal_rank(
            retrieved_keys, relevant_keys
        ),
    }
