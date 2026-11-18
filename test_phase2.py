
from retrievers.retriever import PineconeRetriever


def main():

    print("\n========== PHASE 2 RETRIEVAL TEST ==========")

    retriever = PineconeRetriever(top_k=4)

    question = input("\nEnter your question: ")

    print("\nSearching Pinecone...")

    documents = retriever.retrieve(question)

    if not documents:
        print("\nNo relevant documents found.")
        return

    print("\nRetrieved documents:", len(documents))

    for i, document in enumerate(documents, start=1):

        print(f"\n========== RESULT {i} ==========")

        print("\nContent:")
        print(document.page_content[:700])

        print("\nSource:", document.metadata.get("source"))
        print("Page:", document.metadata.get("page_label",
                                           document.metadata.get("page")))

    print("\n========== PHASE 2 TEST COMPLETED ==========")


if __name__ == "__main__":
    main()
