
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "reports" / "chunking_retrieval_inspection.json"
OUTPUT_FILE = BASE_DIR / "reports" / "chunking_relevance_labels.json"


def create_template():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Inspection report not found: {INPUT_FILE}"
        )

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        report = json.load(file)

    template = {
        "instructions": (
            "Set relevant to true if the chunk contains useful information "
            "for answering the question. Otherwise set it to false."
        ),
        "experiments": []
    }

    for experiment in report["experiments"]:

        experiment_data = experiment["experiment"]

        experiment_template = {
            "name": experiment_data["name"],
            "chunk_size": experiment_data["chunk_size"],
            "chunk_overlap": experiment_data["chunk_overlap"],
            "namespace": experiment_data["namespace"],
            "questions": []
        }

        for question in experiment["questions"]:

            # Only answerable questions are used for
            # relevance-based retrieval metrics.
            if not question["answerable"]:
                continue

            question_template = {
                "question_id": question["question_id"],
                "question": question["question"],
                "expected_answer": question["expected_answer"],
                "candidate_chunks": []
            }

            for result in question["results"]:

                chunk = {
                    "rank": result["rank"],
                    "id": result["id"],
                    "score": result["score"],
                    "page": result["page"],
                    "text": result["text"],
                    "relevant": None
                }

                question_template["candidate_chunks"].append(chunk)

            experiment_template["questions"].append(
                question_template
            )

        template["experiments"].append(experiment_template)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(template, file, indent=4, ensure_ascii=False)

    total_questions = sum(
        len(exp["questions"])
        for exp in template["experiments"]
    )

    total_chunks = sum(
        len(question["candidate_chunks"])
        for exp in template["experiments"]
        for question in exp["questions"]
    )

    print("\nRELEVANCE TEMPLATE CREATED SUCCESSFULLY!")
    print(f"Experiments: {len(template['experiments'])}")
    print(f"Answerable questions: {total_questions}")
    print(f"Candidate chunks: {total_chunks}")
    print(f"\nOutput: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_template()
