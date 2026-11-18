
from pipeline.rag_chain import RAGPipeline
from memory.conversation_memory import ConversationMemory


def display_sources(sources):

    print("\n========== SOURCES ==========")

    if not sources:
        print("No supporting sources found.")
        return

    for source in sources:

        print(f"\n[Source {source['source_id']}]")
        print("Document:", source["document"])
        print("Page:", source["page"])


def main():

    print("\n======================================")
    print("       RAG QUESTION ANSWERING")
    print("======================================")

    rag = RAGPipeline()

    memory = ConversationMemory(max_turns=5)

    print("\nRAG pipeline ready!")
    print("Ask questions about your uploaded documents.")
    print("\nCommands:")
    print("  history - View conversation history")
    print("  clear   - Clear conversation memory")
    print("  exit    - Stop the application")

    while True:

        question = input("\nQuestion: ").strip()

        if question.lower() in ["exit", "quit"]:
            print("\nThank you for using the RAG pipeline!")
            break

        if question.lower() == "history":
            memory.show_history()
            continue

        if question.lower() == "clear":
            memory.clear()
            print("\nConversation memory cleared!")
            continue

        if not question:
            print("Please enter a question.")
            continue

        try:

            result = rag.ask(
                question=question,
                chat_history=memory.get_history(),
            )

            print("\n========== ANSWER ==========")
            print(result["answer"])

            display_sources(result["sources"])

            # Save the completed conversation turn
            memory.add_turn(
                question=question,
                answer=result["answer"],
                sources=result["sources"],
            )

            print("\n============================")

        except Exception as error:

            print(f"\nError: {error}")


if __name__ == "__main__":
    main()
