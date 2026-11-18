
import json
from datetime import datetime
from pathlib import Path

from pipeline.rag_chain import RAGPipeline
from config import TOP_K, SIMILARITY_THRESHOLD


BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports"
REPORT_FILE = REPORT_DIR / "final_validation_report.json"

REFUSAL = "I don't know based on the provided document."


def run_test(pipeline, test_name, question, chat_history=None,
             expect_answerable=True):

    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print(f"QUESTION: {question}")
    print("=" * 70)

    result = pipeline.ask(
        question=question,
        chat_history=chat_history or [],
    )

    answer = result["answer"]
    sources = result.get("sources", [])

    is_refusal = REFUSAL.lower() in answer.lower()

    if expect_answerable:
        passed = (
            not is_refusal
            and result.get("accepted_chunks", 0) > 0
            and len(sources) > 0
        )
    else:
        passed = (
            is_refusal
            and result.get("accepted_chunks", 0) == 0
            and len(sources) == 0
        )

    test_result = {
        "test_name": test_name,
        "question": question,
        "standalone_question": result.get(
            "standalone_question"
        ),
        "answer": answer,
        "expected_answerable": expect_answerable,
        "is_refusal": is_refusal,
        "best_similarity_score": result.get(
            "best_similarity_score"
        ),
        "retrieved_chunks": result.get(
            "retrieved_chunks", 0
        ),
        "accepted_chunks": result.get(
            "accepted_chunks", 0
        ),
        "sources": sources,
        "retrieval_scores": result.get(
            "retrieval_scores", []
        ),
        "source_verification": len(sources) > 0,
        "passed": passed,
    }

    print("\nANSWER:")
    print(answer)

    print("\nRETRIEVAL INFORMATION:")
    print("Best similarity:", result.get("best_similarity_score"))
    print("Retrieved chunks:", result.get("retrieved_chunks"))
    print("Accepted chunks:", result.get("accepted_chunks"))

    print("\nSOURCES:")
    if sources:
        for source in sources:
            print(
                f"Document: {source['document']} | "
                f"Page: {source['page']}"
            )
    else:
        print("No sources returned.")

    print("\nTEST RESULT:", "PASS" if passed else "FAIL")

    return test_result


def main():

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("FINAL RAG PIPELINE VALIDATION")
    print("=" * 70)

    print("Top K:", TOP_K)
    print("Similarity threshold:", SIMILARITY_THRESHOLD)

    pipeline = RAGPipeline()

    results = []

    # -------------------------------------------------
    # TEST 1: Transformer architecture
    # -------------------------------------------------

    test1 = run_test(
        pipeline,
        test_name="Transformer Architecture",
        question="What is the Transformer architecture?",
        expect_answerable=True,
    )
    results.append(test1)

    # -------------------------------------------------
    # TEST 2: Multi-head attention
    # -------------------------------------------------

    test2 = run_test(
        pipeline,
        test_name="Multi-Head Attention",
        question="What is the purpose of multi-head attention?",
        expect_answerable=True,
    )
    results.append(test2)

    # -------------------------------------------------
    # TEST 3: Positional encoding
    # -------------------------------------------------

    test3 = run_test(
        pipeline,
        test_name="Positional Encoding",
        question=(
            "Since the Transformer has no recurrence or convolution, "
            "how does it make use of the order of the sequence?"
        ),
        expect_answerable=True,
    )
    results.append(test3)

    # -------------------------------------------------
    # TEST 4: Unanswerable question
    # -------------------------------------------------

    test4 = run_test(
        pipeline,
        test_name="Unrelated Question Rejection",
        question="How does photosynthesis work in plants?",
        expect_answerable=False,
    )
    results.append(test4)

    # -------------------------------------------------
    # TEST 5: Conversational follow-up
    # -------------------------------------------------

    history = [
        {
            "question": test3["question"],
            "answer": test3["answer"],
        }
    ]

    test5 = run_test(
        pipeline,
        test_name="Conversational Follow-up",
        question="Why is that necessary?",
        chat_history=history,
        expect_answerable=True,
    )
    results.append(test5)

    # -------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------

    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed

    report = {
        "generated_at": datetime.now().isoformat(),
        "configuration": {
            "chunk_size": 500,
            "chunk_overlap": 50,
            "top_k": TOP_K,
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "embedding_model": "all-MiniLM-L6-v2",
            "namespace": "rag-combined-v2",
        },
        "summary": {
            "total_tests": len(results),
            "passed": passed,
            "failed": failed,
            "success_rate": round(
                (passed / len(results)) * 100, 2
            ),
        },
        "tests": results,
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 70)

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{result['test_name']}: {status}")

    print("-" * 70)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {report['summary']['success_rate']}%")

    print("\nReport saved at:")
    print(REPORT_FILE)

    print("\nFINAL VALIDATION COMPLETED!")


if __name__ == "__main__":
    main()
