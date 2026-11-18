
import json
from pathlib import Path

from evaluation.evaluation_dataset import EVALUATION_DATASET
from evaluation.answer_evaluator import AnswerEvaluator
from pipeline.rag_chain import RAGPipeline


BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"


def main():

    REPORT_DIR.mkdir(exist_ok=True)

    print("\n===== RAG ANSWER EVALUATION =====")

    pipeline = RAGPipeline()
    evaluator = AnswerEvaluator()

    results = []

    dataset = [
        item
        for item in EVALUATION_DATASET
        if item["answerable"]
    ]

    for item in dataset:

        question = item["question"]

        print("\n" + "=" * 70)
        print(f"Question {item['id']}: {question}")
        print("=" * 70)

        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        with open(REPORT_DIR / "answer_evaluation.json", "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4, ensure_ascii=False)

        print("\nProgress saved successfully.")

        # Generate answer using RAG
        rag_result = pipeline.ask(question)

        answer = rag_result["answer"]
        context = rag_result.get("context", "")

        print("\nGenerated Answer:")
        print(answer)

        # Evaluate the generated answer
        evaluation = evaluator.evaluate(
            question=question,
            context=context,
            answer=answer,
            expected_answer=item["expected_answer"],
        )

        print("\nEvaluation:")
        print(
            "Faithfulness:",
            evaluation["faithfulness_score"],
            "/ 5"
        )

        print(
            "Answer Relevance:",
            evaluation["relevance_score"],
            "/ 5"
        )

        print(
            "Faithfulness Reason:",
            evaluation["faithfulness_reason"]
        )

        print(
            "Relevance Reason:",
            evaluation["relevance_reason"]
        )

        print(
            "Result:",
            "PASS" if evaluation["passed"] else "NEEDS IMPROVEMENT"
        )

        results.append({
            "question_id": item["id"],
            "question": question,
            "answer": answer,
            "sources": rag_result["sources"],
            "evaluation": evaluation,
        })

    # Calculate average scores
    total = len(results)

    if total == 0:
        print("No answerable questions found.")
        return

    average_faithfulness = sum(
        item["evaluation"]["faithfulness_score"]
        for item in results
    ) / total

    average_relevance = sum(
        item["evaluation"]["relevance_score"]
        for item in results
    ) / total

    passed = sum(
        item["evaluation"]["passed"]
        for item in results
    )

    report = {
        "total_questions": total,
        "average_faithfulness": round(
            average_faithfulness, 2
        ),
        "average_relevance": round(
            average_relevance, 2
        ),
        "passed_questions": passed,
        "failed_questions": total - passed,
        "results": results,
    }

    report_path = REPORT_DIR / "answer_evaluation.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("===== FINAL EVALUATION SUMMARY =====")
    print("=" * 70)

    print(f"Total Questions: {total}")
    print(f"Average Faithfulness: {average_faithfulness:.2f}/5")
    print(f"Average Relevance: {average_relevance:.2f}/5")
    print(f"Passed: {passed}")
    print(f"Needs Improvement: {total - passed}")

    print(f"\nReport saved at: {report_path}")


if __name__ == "__main__":
    main()
