
from config import TOP_K, SIMILARITY_THRESHOLD

from retrievers.retriever import PineconeRetriever
from llms.groq_llm import GroqLLM

from prompts.rag_prompt import (
    SYSTEM_PROMPT,
    CONTEXTUALIZE_SYSTEM_PROMPT,
    build_user_prompt,
    build_contextualization_prompt,
)


class RAGPipeline:

    def __init__(
        self,
        top_k=TOP_K,
        similarity_threshold=SIMILARITY_THRESHOLD,
    ):

        print("Initializing RAG Pipeline...")

        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(
                "Similarity threshold must be between 0.0 and 1.0"
            )

        self.retriever = PineconeRetriever(top_k=top_k)
        self.llm = GroqLLM()
        self.similarity_threshold = similarity_threshold

        print(
            f"Similarity threshold: {self.similarity_threshold}"
        )

        print("RAG Pipeline initialized successfully!")

    @staticmethod
    def build_context(documents):

        context_parts = []
        sources = []

        for index, document in enumerate(documents, start=1):

            metadata = document.metadata

            source_path = metadata.get(
                "source", "Unknown source"
            )

            page = metadata.get(
                "page_label",
                metadata.get("page", "Unknown"),
            )

            source_name = (
                source_path.replace("\\", "/").split("/")[-1]
            )

            context_parts.append(
                f"""
[Source {index}]
Document: {source_name}
Page: {page}

Content:
{document.page_content}
"""
            )

            sources.append({
                "source_id": index,
                "document": source_name,
                "page": page,
                "path": source_path,
            })

        return "\n\n".join(context_parts), sources

    def contextualize_question(self, question, chat_history):

        if not chat_history:
            return question

        history_text = "\n\n".join(
            f"User: {turn['question']}\n"
            f"Assistant: {turn['answer']}"
            for turn in chat_history
        )

        prompt = build_contextualization_prompt(
            question=question,
            chat_history=history_text,
        )

        standalone_question = self.llm.generate(
            system_prompt=CONTEXTUALIZE_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        standalone_question = standalone_question.strip()

        return standalone_question or question

    def ask(self, question, chat_history=None):

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        chat_history = chat_history or []

        print("\nUnderstanding conversation context...")

        standalone_question = self.contextualize_question(
            question=question,
            chat_history=chat_history,
        )

        if standalone_question != question:
            print(
                "Contextualized question:",
                standalone_question,
            )

        print("\nRetrieving relevant document chunks...")

        # Retrieve documents along with their similarity scores
        retrieval_results = self.retriever.retrieve_with_scores(
            standalone_question
        )

        # Filter chunks using the configured threshold
        filtered_results = [
            result
            for result in retrieval_results
            if (
                result["score"] is not None
                and result["score"] >= self.similarity_threshold
            )
        ]

        print(
            f"Retrieved chunks: {len(retrieval_results)}"
        )

        print(
            f"Chunks passing threshold: {len(filtered_results)}"
        )

        # Reject if no chunks are sufficiently relevant
        if not filtered_results:

            best_score = (
                retrieval_results[0]["score"]
                if retrieval_results
                else None
            )

            print(
                "No relevant document chunks found."
            )

            return {
                "answer": (
                    "I don't know based on the provided document."
                ),
                "sources": [],
                "standalone_question": standalone_question,
                "best_similarity_score": best_score,
                "retrieved_chunks": len(retrieval_results),
                "accepted_chunks": 0,
                "retrieval_scores": [],
                "context": "",
            }

        documents = [
            result["document"]
            for result in filtered_results
        ]

        context, sources = self.build_context(documents)

        # Include retrieval scores for evaluation and inspection
        retrieval_scores = [
            {
                "vector_id": result["id"],
                "score": result["score"],
            }
            for result in filtered_results
        ]

        user_prompt = build_user_prompt(
            question=standalone_question,
            context=context,
        )

        print("\nGenerating answer using Groq...")

        answer = self.llm.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        return {
            "answer": answer,
            "sources": sources,
            "standalone_question": standalone_question,
            "best_similarity_score": retrieval_results[0]["score"],
            "retrieved_chunks": len(retrieval_results),
            "accepted_chunks": len(filtered_results),
            "retrieval_scores": retrieval_scores,
            "context": context,
        }