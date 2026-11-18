import time
from groq import RateLimitError
import json

from llms.groq_llm import GroqLLM


class AnswerEvaluator:

    def __init__(self):

        self.llm = GroqLLM()

    def evaluate(
        self,
        question,
        context,
        answer,
        expected_answer,
    ):

        system_prompt = """
You are an expert evaluator for a Retrieval Augmented Generation system.

Evaluate the generated answer using the supplied document context
and expected answer.

Evaluate two dimensions:

1. Faithfulness:
   - Is the generated answer supported by the document context?
   - Are there unsupported claims or invented facts?
   - Score from 1 to 5.

2. Answer Relevance:
   - Does the answer correctly address the user's question?
   - Does it cover the important information in the expected answer?
   - Score from 1 to 5.

Scoring:
5 = Excellent
4 = Good
3 = Partially correct
2 = Poor
1 = Incorrect

Important:
- Do not reward unsupported information.
- Do not penalize an answer for using different wording.
- The document context is the source of truth.
- The expected answer is a reference for relevance, not a source of facts.

Return ONLY valid JSON in this exact structure:

{
    "faithfulness_score": 1,
    "relevance_score": 1,
    "faithfulness_reason": "Explanation",
    "relevance_reason": "Explanation"
}
"""

        user_prompt = f"""
QUESTION:
{question}

DOCUMENT CONTEXT:
{context}

EXPECTED ANSWER:
{expected_answer}

GENERATED ANSWER:
{answer}

Evaluate the generated answer.
"""

        max_retries = 5
        response = None

        for attempt in range(max_retries):
            try:
                response = self.llm.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                break

            except RateLimitError:
                if attempt == max_retries - 1:
                    raise

                wait_time = 2 ** (attempt + 1)

                print(
                    f"Groq rate limit reached. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

        try:
            # Extract JSON even if the model adds surrounding text
            start = response.find("{")
            end = response.rfind("}")

            if start == -1 or end == -1:
                raise ValueError("No JSON object found.")

            result = json.loads(response[start:end + 1])

            faithfulness = float(
                result["faithfulness_score"]
            )

            relevance = float(
                result["relevance_score"]
            )

            if not 1 <= faithfulness <= 5:
                raise ValueError(
                    "Faithfulness score must be between 1 and 5."
                )

            if not 1 <= relevance <= 5:
                raise ValueError(
                    "Relevance score must be between 1 and 5."
                )

            return {
                "faithfulness_score": faithfulness,
                "relevance_score": relevance,
                "faithfulness_reason": result[
                    "faithfulness_reason"
                ],
                "relevance_reason": result[
                    "relevance_reason"
                ],
                "passed": (
                    faithfulness >= 4
                    and relevance >= 4
                ),
            }

        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:

            raise RuntimeError(
                f"Answer evaluation failed: {error}. "
                f"Model response: {response}"
            ) from error
