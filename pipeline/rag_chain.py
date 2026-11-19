from config import TOP_K, SIMILARITY_THRESHOLD

from retrievers.retriever import PineconeRetriever
from llms.groq_llm import GroqLLM

from prompts.rag_prompt import (
    SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    CONTEXTUALIZE_SYSTEM_PROMPT,
    build_user_prompt,
    build_summary_prompt,
    build_contextualization_prompt,
)

from rag.constants import (
    QUESTION_TYPE_SUMMARY,
    REFUSAL_MESSAGE,
)
from rag.question_classifier import classify_question
from rag.retrieval import RetrievalOrchestrator
from rag.relevance_checker import validate_relevance
from rag.source_validator import (
    build_sources,
    mark_cited_sources,
    grounding_score,
)
from rag.confidence import assess_confidence


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
        self.retrieval = RetrievalOrchestrator(
            retriever=self.retriever,
            top_k=top_k,
        )
        self.llm = GroqLLM()
        self.similarity_threshold = similarity_threshold

        print(
            f"Similarity threshold: {self.similarity_threshold}"
        )

        print("RAG Pipeline initialized successfully!")

    @staticmethod
    def build_context(documents):

        context_parts = []

        for index, document in enumerate(documents, start=1):
            metadata = document.metadata
            source_name = metadata.get("document_name") or (
                str(metadata.get("source", "Unknown source"))
                .replace("\\", "/")
                .split("/")[-1]
            )
            if metadata.get("page_label") is not None:
                page = metadata["page_label"]
            else:
                page = metadata.get("page", "Unknown")
                if isinstance(page, int):
                    page += 1

            context_parts.append(
                f"""
[Source {index}]
Document: {source_name}
Page: {page}

Content:
{document.page_content}
"""
            )

        return "\n\n".join(context_parts)

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

    def _refusal_result(
        self,
        question_type,
        standalone_question,
        retrieval_results,
        reason,
    ):

        best_score = (
            retrieval_results[0]["score"]
            if retrieval_results
            else None
        )

        return {
            "status": "rejected",
            "answer": REFUSAL_MESSAGE,
            "question_type": question_type,
            "confidence": assess_confidence(
                question_type=question_type,
                accepted_results=[],
                citation_report={},
                grounding=0.0,
                refused=True,
                threshold=self.similarity_threshold,
            ),
            "sources": [],
            "related_questions": [],
            "standalone_question": standalone_question,
            "best_similarity_score": best_score,
            "retrieved_chunks": len(retrieval_results),
            "accepted_chunks": 0,
            "retrieval_scores": [],
            "relevance_reason": reason,
            "context": "",
        }

    def ask(
        self,
        question,
        chat_history=None,
        document_ids=None,
        user_id=None,
    ):

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

        question_type = classify_question(standalone_question)
        print(f"Question type: {question_type}")

        print("\nRetrieving relevant document chunks...")

        retrieval_results = self.retrieval.retrieve(
            question=standalone_question,
            question_type=question_type,
            document_ids=document_ids,
            user_id=user_id,
        )

        relevance = validate_relevance(
            question=standalone_question,
            question_type=question_type,
            retrieval_results=retrieval_results,
            threshold=self.similarity_threshold,
        )

        filtered_results = relevance["accepted"]

        print(f"Retrieved chunks: {len(retrieval_results)}")
        print(f"Chunks passing validation: {len(filtered_results)}")
        print(f"Relevance: {relevance['reason']}")

        if not relevance["is_relevant"]:
            print("No relevant document evidence found.")
            return self._refusal_result(
                question_type=question_type,
                standalone_question=standalone_question,
                retrieval_results=retrieval_results,
                reason=relevance["reason"],
            )

        documents = [
            result["document"]
            for result in filtered_results
        ]

        context = self.build_context(documents)
        sources = build_sources(filtered_results)

        retrieval_scores = [
            {
                "vector_id": result["id"],
                "score": result["score"],
            }
            for result in filtered_results
        ]

        if question_type == QUESTION_TYPE_SUMMARY:
            system_prompt = SUMMARY_SYSTEM_PROMPT
            user_prompt = build_summary_prompt(
                question=standalone_question,
                context=context,
            )
        else:
            system_prompt = SYSTEM_PROMPT
            user_prompt = build_user_prompt(
                question=standalone_question,
                context=context,
            )

        print("\nGenerating answer using Groq...")

        answer = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        refused = answer.strip() == REFUSAL_MESSAGE
        citation_report = mark_cited_sources(sources, answer)
        grounding = grounding_score(answer, context, REFUSAL_MESSAGE)
        confidence = assess_confidence(
            question_type=question_type,
            accepted_results=filtered_results,
            citation_report=citation_report,
            grounding=grounding,
            refused=refused,
            threshold=self.similarity_threshold,
        )

        return {
            "status": "rejected" if refused else "success",
            "answer": answer,
            "question_type": question_type,
            "confidence": confidence,
            "sources": sources,
            "related_questions": [],
            "standalone_question": standalone_question,
            "best_similarity_score": retrieval_results[0]["score"]
            if retrieval_results else None,
            "retrieved_chunks": len(retrieval_results),
            "accepted_chunks": len(filtered_results),
            "retrieval_scores": retrieval_scores,
            "relevance_reason": relevance["reason"],
            "citation_report": citation_report,
            "context": context,
        }
