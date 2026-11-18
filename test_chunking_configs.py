
from pathlib import Path

from loaders.document_loader import load_documents
from splitters.text_splitter import split_documents


EXPERIMENTS = [
    {
        "name": "A - Baseline",
        "chunk_size": 500,
        "chunk_overlap": 50,
    },
    {
        "name": "B - Medium",
        "chunk_size": 700,
        "chunk_overlap": 100,
    },
    {
        "name": "C - Large",
        "chunk_size": 1000,
        "chunk_overlap": 150,
    },
]


def main():

    print("\n========== CHUNKING COMPARISON ==========")

    documents = load_documents(Path("data/raw"))

    print("Documents loaded:", len(documents))

    for experiment in EXPERIMENTS:

        print("\n----------------------------------------")
        print(experiment["name"])

        chunks = split_documents(
            documents,
            chunk_size=experiment["chunk_size"],
            chunk_overlap=experiment["chunk_overlap"],
        )

        lengths = [len(chunk.page_content) for chunk in chunks]

        average_length = sum(lengths) / len(lengths)

        print("Chunk size:", experiment["chunk_size"])
        print("Chunk overlap:", experiment["chunk_overlap"])
        print("Total chunks:", len(chunks))
        print("Average chunk length:", round(average_length, 2))
        print("Minimum chunk length:", min(lengths))
        print("Maximum chunk length:", max(lengths))

    print("\n========== COMPARISON COMPLETED ==========")


if __name__ == "__main__":
    main()
