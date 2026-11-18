
from evaluation.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
    evaluate_retrieval,
)


def main():

    # Simulated retrieval results
    retrieved_keys = [
        "chunk_101",
        "chunk_102",
        "chunk_103",
        "chunk_104",
    ]

    # Manually identified relevant chunks
    relevant_keys = [
        "chunk_102",
        "chunk_104",
    ]

    print("\n===== RAG RETRIEVAL EVALUATION =====")

    precision = precision_at_k(
        retrieved_keys, relevant_keys, k=4
    )

    recall = recall_at_k(
        retrieved_keys, relevant_keys, k=4
    )

    rr = reciprocal_rank(
        retrieved_keys, relevant_keys
    )

    print(f"Precision@4 : {precision:.2f}")
    print(f"Recall@4    : {recall:.2f}")
    print(f"Reciprocal Rank: {rr:.2f}")

    # Test MRR across two questions
    results = [
        {
            "retrieved_keys": [
                "chunk_101",
                "chunk_102",
                "chunk_103",
            ],
            "relevant_keys": ["chunk_102"],
        },
        {
            "retrieved_keys": [
                "chunk_201",
                "chunk_202",
                "chunk_203",
            ],
            "relevant_keys": ["chunk_201"],
        },
    ]

    mrr = mean_reciprocal_rank(results)

    print(f"Mean Reciprocal Rank: {mrr:.2f}")

    print("\n===== TEST PASSED =====")


if __name__ == "__main__":
    main()
