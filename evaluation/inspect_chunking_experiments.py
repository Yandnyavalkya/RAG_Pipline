
import json
from pathlib import Path
from datetime import datetime

from config import TOP_K
from retrievers.retriever import PineconeRetriever
from evaluation.evaluation_dataset import EVALUATION_DATASET


EXPERIMENTS = [
    {
        "name": "A - Baseline",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "namespace": "rag-chunk-500-50",
    },
    {
        "name": "B - Medium",
        "chunk_size": 700,
        "chunk_overlap": 100,
        "namespace": "rag-chunk-700-100",
    },
    {
        "name": "C - Large",
        "chunk_size": 1000,
        "chunk_overlap": 150,
        "namespace": "rag-chunk-1000-150",
    },
]


def main():

    print("\n========== CHUNKING RETRIEVAL INSPECTION ==========")
    print("TOP_K:", TOP_K)

    all_results = []

    for experiment in EXPERIMENTS:

        print("\n\n========================================")
        print("EXPERIMENT:", experiment["name"])
        print("Namespace:", experiment["namespace"])
        print("========================================")

        retriever = PineconeRetriever(
            top_k=TOP_K,
            namespace=experiment["namespace"],
        )

        experiment_results = []

        for item in EVALUATION_DATASET:

            question = item["question"]

            print("\n----------------------------------------")
            print(f"Question {item['id']}: {question}")
            print("----------------------------------------")

            results = retriever.retrieve_with_scores(question)

            question_results = []

            if not results:
                print("No results returned.")

            for rank, result in enumerate(results, start=1):

                document = result["document"]
                metadata = document.metadata

                record = {
                    "rank": rank,
                    "id": result["id"],
                    "score": result["score"],
                    "source": metadata.get("source", "Unknown"),
                    "page": metadata.get(
                        "page_label",
                        metadata.get("page", "Unknown"),
                    ),
                    "text": document.page_content,
                }

                question_results.append(record)

                print(f"\nRank: {rank}")
                print("Vector ID:", record["id"])
                print("Similarity:", round(record["score"], 4))
                print("Source:", record["source"])
                print("Page:", record["page"])
                print("Text preview:")
                print(document.page_content[:350].replace("\n", " "))

            experiment_results.append({
                "question_id": item["id"],
                "question": question,
                "answerable": item["answerable"],
                "expected_answer": item["expected_answer"],
                "results": question_results,
            })

        all_results.append({
            "experiment": experiment,
            "questions": experiment_results,
        })

    output = {
        "generated_at": datetime.now().isoformat(),
        "top_k": TOP_K,
        "experiments": all_results,
    }

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    output_path = reports_dir / "chunking_retrieval_inspection.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=4, ensure_ascii=False)

    print("\n\n========== INSPECTION COMPLETED ==========")
    print("Report saved to:", output_path)


if __name__ == "__main__":
    main()
