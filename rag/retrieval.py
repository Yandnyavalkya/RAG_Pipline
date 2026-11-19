from rag.constants import QUESTION_TYPE_SUMMARY, SUMMARY_PROBES


def build_metadata_filter(document_ids=None, user_id=None):
    clauses = []

    unique_ids = [value for value in (document_ids or []) if value]
    if len(unique_ids) == 1:
        clauses.append({"document_id": {"$eq": unique_ids[0]}})
    elif unique_ids:
        clauses.append({"document_id": {"$in": unique_ids}})

    if user_id:
        clauses.append({"user_id": {"$eq": user_id}})

    if not clauses:
        return None

    if len(clauses) == 1:
        return clauses[0]

    return {"$and": clauses}


def _page_sort_key(page_value):
    try:
        return int(float(str(page_value)))
    except (TypeError, ValueError):
        return 10_000


def _merge_results(result_lists):
    merged = {}

    for results in result_lists:
        for result in results:
            vector_id = result.get("id")
            if not vector_id:
                continue

            existing = merged.get(vector_id)
            if existing is None or (
                (result.get("score") or 0)
                > (existing.get("score") or 0)
            ):
                merged[vector_id] = result

    return list(merged.values())


def diversify_by_page(results, top_k):
    grouped = {}

    ranked = sorted(
        results,
        key=lambda item: item.get("score") or 0,
        reverse=True,
    )

    for result in ranked:
        document = result.get("document")
        metadata = document.metadata if document is not None else {}
        page = metadata.get("page_label", metadata.get("page", "Unknown"))
        grouped.setdefault(str(page), []).append(result)

    diversified = []

    for page in sorted(grouped.keys(), key=_page_sort_key):
        diversified.append(grouped[page][0])
        if len(diversified) >= top_k:
            return diversified

    return diversified[:top_k]


class RetrievalOrchestrator:
    """Question-type aware retrieval that keeps the calibrated threshold."""

    def __init__(self, retriever, top_k):
        self.retriever = retriever
        self.top_k = top_k

    def retrieve(
        self,
        question,
        question_type,
        document_ids=None,
        user_id=None,
    ):
        metadata_filter = build_metadata_filter(
            document_ids=document_ids,
            user_id=user_id,
        )

        if question_type == QUESTION_TYPE_SUMMARY:
            return self._retrieve_representative(
                question=question,
                metadata_filter=metadata_filter,
            )

        return self.retriever.retrieve_with_scores(
            question,
            metadata_filter=metadata_filter,
            top_k=self.top_k,
        )

    def _retrieve_representative(self, question, metadata_filter):
        probes = [question, *SUMMARY_PROBES]
        result_lists = []

        for probe in probes:
            result_lists.append(
                self.retriever.retrieve_with_scores(
                    probe,
                    metadata_filter=metadata_filter,
                    top_k=self.top_k,
                )
            )

        merged = _merge_results(result_lists)
        return diversify_by_page(merged, self.top_k)
