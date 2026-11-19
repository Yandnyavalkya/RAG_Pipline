from pipeline.rag_chain import RAGPipeline
from memory.conversation_memory import ConversationMemory


def display_confidence(confidence):

    print("\n========== CONFIDENCE ==========")

    if not confidence:
        print("Confidence unavailable.")
        return

    print("Level:", confidence.get("level"))
    print("Calibrated score:", confidence.get("score"))

    signals = confidence.get("signals") or {}
    if signals:
        print("Signals:")
        for name, value in signals.items():
            print(f"  {name}: {value}")


def display_sources(sources):

    print("\n========== SOURCES ==========")

    if not sources:
        print("No supporting sources found.")
        return

    for source in sources:

        cited = "cited" if source.get("cited") else "retrieved"
        print(f"\n[Source {source['source_id']}: {source['document']}, Page {source['page']}]")
        print("Chunk ID:", source.get("chunk_id"))
        print("Status:", cited)
        if source.get("excerpt"):
            print("Excerpt:", source["excerpt"])


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
            print("Status:", result.get("status"))
            print("Question type:", result.get("question_type"))
            print(result["answer"])

            display_confidence(result.get("confidence"))
            display_sources(result["sources"])

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
