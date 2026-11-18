
from retrievers.retriever import PineconeRetriever
from evaluation.evaluation_dataset import EVALUATION_DATASET


def main():

    print("\n===== REAL PINECONE RETRIEVAL INSPECTION =====")

    retriever = PineconeRetriever(top_k=4)

    for item in EVALUATION_DATASET:

        question = item["question"]

        print("\n" + "=" * 80)
        print(f"Question ID: {item['id']}")
        print(f"Question: {question}")
        print(f"Expected answerable: {item['answerable']}")
        print("=" * 80)

        results = retriever.retrieve_with_scores(question)

        if not results:
            print("No documents retrieved.")
            continue

        for rank, result in enumerate(results, start=1):

            document = result["document"]
            metadata = document.metadata

            print(f"\nRank: {rank}")
            print(f"Vector ID: {result['id']}")
            print(f"Similarity Score: {result['score']}")

            print(
                f"Source: {metadata.get('source', 'Unknown')}"
            )

            print(
                f"Page: {metadata.get('page', 'Unknown')}"
            )

            print("\nChunk Preview:")

            print(
                document.page_content[:350].replace("\n", " ")
            )

            print("-" * 60)


if __name__ == "__main__":
    main()
